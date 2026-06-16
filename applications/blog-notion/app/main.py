"""FastAPI entrypoint: pages, image proxy, and the Notion webhook."""
import hashlib
import hmac
import math
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .cache import Cache
from .config import get_settings
from .notion import NotionClient
from .render import placeholder_svg, render_blocks, summary_from_blocks

# Sort options exposed in the UI: key -> (label, sort function).
SORTS = {
    "newest": ("Newest", lambda p: p["updated"], True),
    "oldest": ("Oldest", lambda p: p["updated"], False),
    "az": ("A–Z", lambda p: p["title"].lower(), False),
}
DEFAULT_SORT = "newest"

settings = get_settings()
notion = NotionClient(settings)
cache = Cache(settings)
templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.close()
    await notion.close()


app = FastAPI(title=settings.site_title, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _ctx(request: Request, **extra) -> dict:
    base = {
        "request": request,
        "site_title": settings.site_title,
        "site_description": settings.site_description,
        "site_author": settings.site_author,
    }
    base.update(extra)
    return base


async def _all_posts() -> list[dict]:
    """Post list, cached."""
    cached = await cache.get_json("posts")
    if cached is not None:
        return cached
    posts = await notion.list_posts()
    await cache.set_json(posts, "posts")
    return posts


async def _post_by_id(page_id: str) -> dict | None:
    for post in await _all_posts():
        if post["id"] == page_id:
            return post
    return None


# ---- Pages ---------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = 1, sort: str = DEFAULT_SORT):
    if sort not in SORTS:
        sort = DEFAULT_SORT
    _, key, reverse = SORTS[sort]
    posts = sorted(await _all_posts(), key=key, reverse=reverse)

    per = settings.page_size
    pages = max(1, math.ceil(len(posts) / per))
    page = max(1, min(page, pages))
    start = (page - 1) * per
    page_posts = posts[start:start + per]

    return templates.TemplateResponse(
        "index.html",
        _ctx(
            request,
            posts=page_posts,
            page=page,
            pages=pages,
            sort=sort,
            sorts={k: v[0] for k, v in SORTS.items()},
        ),
    )


@app.get("/tag/{tag}", response_class=HTMLResponse)
async def by_tag(request: Request, tag: str):
    posts = [p for p in await _all_posts() if tag in p["tags"]]
    return templates.TemplateResponse(
        "tag.html", _ctx(request, tag=tag, posts=posts)
    )


@app.get("/p/{slug}", response_class=HTMLResponse)
async def post_page(request: Request, slug: str):
    cached = await cache.get_json("post", slug)
    if cached is None:
        post = await notion.get_post_by_slug(slug)
        if not post:
            raise StarletteHTTPException(status_code=404, detail="Not found")
        blocks = await notion.get_blocks(post["id"])
        cached = {
            "post": post,
            "html": render_blocks(blocks),
            "summary": summary_from_blocks(blocks),
        }
        await cache.set_json(cached, "post", slug)
    return templates.TemplateResponse(
        "post.html",
        _ctx(request, post=cached["post"], body=cached["html"], summary=cached["summary"]),
    )


# ---- Cover & image proxy -------------------------------------------------

async def _fetch_image(url: str) -> httpx.Response | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            return await client.get(url, follow_redirects=True)
    except httpx.HTTPError:
        return None


@app.get("/cover/{page_id}")
async def cover_proxy(page_id: str):
    """Serve a post's Notion cover, or a generated gradient if it has none."""
    post = await _post_by_id(page_id)
    url = post.get("cover_url") if post else None

    if url:
        resp = await _fetch_image(url)
        # Signed Notion URLs expire; refetch a fresh one and retry once.
        if resp is not None and resp.status_code == 403:
            url = await notion.get_cover_url(page_id)
            resp = await _fetch_image(url) if url else None
        if resp is not None and resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=3600"},
            )

    return Response(
        content=placeholder_svg(page_id),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/img/{block_id}")
async def image_proxy(block_id: str):
    """Resolve and stream a Notion image so expiring signed URLs never leak."""
    url = await notion.get_image_url(block_id)
    if not url:
        return Response(status_code=404)
    async with httpx.AsyncClient(timeout=15.0) as client:
        upstream = await client.get(url, follow_redirects=True)
    return Response(
        content=upstream.content,
        media_type=upstream.headers.get("content-type", "image/png"),
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ---- Notion webhook ------------------------------------------------------

@app.post("/webhooks/notion")
async def notion_webhook(request: Request):
    body = await request.body()

    # First-time handshake: Notion sends a one-off verification_token. Log it so
    # you can paste it into NOTION_WEBHOOK_SECRET.
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if isinstance(payload, dict) and payload.get("verification_token"):
        token = payload["verification_token"]
        print(f"[notion-webhook] verification_token: {token}", flush=True)
        return JSONResponse({"verification_token_received": True})

    # Verify signature when a secret is configured.
    if settings.notion_webhook_secret:
        sig = request.headers.get("X-Notion-Signature", "")
        expected = "sha256=" + hmac.new(
            settings.notion_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return JSONResponse({"error": "invalid signature"}, status_code=401)

    cleared = await cache.invalidate_all()
    print(f"[notion-webhook] cache invalidated ({cleared} keys)", flush=True)
    return JSONResponse({"ok": True, "invalidated": cleared})


# ---- Health & errors -----------------------------------------------------

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "mock": settings.use_mock}


@app.exception_handler(StarletteHTTPException)
async def not_found(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html", _ctx(request), status_code=404
        )
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)
