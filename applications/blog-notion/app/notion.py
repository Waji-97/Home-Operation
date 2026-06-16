"""Thin async Notion API client.

Exposes the two operations the site needs — list published posts and fetch a
page's blocks — plus a helper to resolve a fresh image URL for the proxy.
Falls back to built-in mock content when no credentials are configured.
"""
import httpx

from .config import Settings
from . import mock

API_BASE = "https://api.notion.com/v1"


class NotionClient:
    def __init__(self, settings: Settings):
        self.s = settings
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=API_BASE,
                headers={
                    "Authorization": f"Bearer {self.s.notion_token}",
                    "Notion-Version": self.s.notion_version,
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # -- property extraction helpers --------------------------------------

    def _prop_plain(self, props: dict, name: str) -> str:
        prop = props.get(name, {})
        ptype = prop.get("type")
        if ptype == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", []))
        if ptype == "rich_text":
            return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
        if ptype == "select":
            sel = prop.get("select")
            return sel.get("name", "") if sel else ""
        return ""

    def _prop_tags(self, props: dict, name: str) -> list[str]:
        prop = props.get(name, {})
        if prop.get("type") == "multi_select":
            return [t.get("name", "") for t in prop.get("multi_select", [])]
        return []

    def _prop_updated(self, page: dict, name: str) -> str:
        prop = page.get("properties", {}).get(name, {})
        if prop.get("type") in ("last_edited_time", "created_time"):
            return prop.get(prop["type"], "")
        if prop.get("type") == "date":
            d = prop.get("date")
            return d.get("start", "") if d else ""
        # Fall back to the page's own last_edited_time.
        return page.get("last_edited_time", "")

    def _cover_url(self, page: dict) -> str | None:
        cover = page.get("cover")
        if not cover:
            return None
        if cover.get("type") == "external":
            return cover["external"]["url"]
        if cover.get("type") == "file":
            return cover["file"]["url"]
        return None

    def _page_to_post(self, page: dict) -> dict:
        props = page.get("properties", {})
        return {
            "id": page["id"],
            "title": self._prop_plain(props, self.s.prop_title) or "Untitled",
            "slug": self._prop_plain(props, self.s.prop_slug),
            "status": self._prop_plain(props, self.s.prop_status),
            "type": self._prop_plain(props, self.s.prop_type),
            "tags": self._prop_tags(props, self.s.prop_tags),
            "updated": self._prop_updated(page, self.s.prop_updated),
            "cover_url": self._cover_url(page),
        }

    # -- public API --------------------------------------------------------

    async def list_posts(self) -> list[dict]:
        """All public posts, newest first."""
        if self.s.use_mock:
            posts = [p for p in mock.MOCK_POSTS if p["status"] == self.s.status_public_value]
            return sorted(posts, key=lambda p: p["updated"], reverse=True)

        http = await self._http()
        results: list[dict] = []
        payload = {
            "filter": {
                "property": self.s.prop_status,
                "select": {"equals": self.s.status_public_value},
            },
            "sorts": [{"property": self.s.prop_updated, "direction": "descending"}],
            "page_size": 100,
        }
        cursor = None
        while True:
            if cursor:
                payload["start_cursor"] = cursor
            resp = await http.post(
                f"/databases/{self.s.notion_database_id}/query", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            results.extend(self._page_to_post(p) for p in data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return [p for p in results if p["slug"]]

    async def get_post_by_slug(self, slug: str) -> dict | None:
        for post in await self.list_posts():
            if post["slug"] == slug:
                return post
        return None

    async def get_blocks(self, page_id: str) -> list[dict]:
        """Flat list of a page's child blocks (one level — good enough for posts)."""
        if self.s.use_mock:
            return mock.MOCK_BLOCKS.get(page_id, [])

        http = await self._http()
        blocks: list[dict] = []
        cursor = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            resp = await http.get(f"/blocks/{page_id}/children", params=params)
            resp.raise_for_status()
            data = resp.json()
            blocks.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return blocks

    async def get_cover_url(self, page_id: str) -> str | None:
        """Resolve a fresh cover URL for a page (used when a cached signed URL expires)."""
        if self.s.use_mock:
            return None
        http = await self._http()
        resp = await http.get(f"/pages/{page_id}")
        resp.raise_for_status()
        return self._cover_url(resp.json())

    async def get_image_url(self, block_id: str) -> str | None:
        """Resolve the current (fresh) URL for an image block."""
        if self.s.use_mock:
            return None
        http = await self._http()
        resp = await http.get(f"/blocks/{block_id}")
        resp.raise_for_status()
        block = resp.json()
        img = block.get("image", {})
        if img.get("type") == "external":
            return img["external"]["url"]
        if img.get("type") == "file":
            return img["file"]["url"]
        return None
