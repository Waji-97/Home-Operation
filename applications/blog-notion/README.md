# blog-notion

A personal blog + notes site that uses **Notion as a live headless CMS**, served
by **FastAPI + Jinja2**, cached in **Redis**, and deployed to **Kubernetes**.

You write in Notion. When you hit *Publish*, a Notion webhook busts the cache and
the change is live in seconds — without querying the Notion API on every request.

```
Notion (you edit) ──webhook──▶ FastAPI ──invalidate──▶ Redis
        ▲                          │                     │
        └────── API fetch ─────────┘   serves from cache ┘
```

## How content maps to Notion

One Notion database, one row per post. Columns used (names configurable in `.env`):

| Column     | Type          | Used for                                  |
|------------|---------------|-------------------------------------------|
| `title`    | Title         | Post title                                |
| `slug`     | Text          | URL: `/p/<slug>`                          |
| `status`   | Select        | Only `Public` rows are shown              |
| `type`     | Select        | `Post` → Blog section, `Note` → Notes     |
| `tags`     | Multi-select  | Tag pages at `/tag/<tag>`                 |
| `updated`  | Last edited   | Sort order + displayed date               |

The card blurb is auto-derived from each post's first paragraph (no extra column).

## Run locally

No Notion credentials needed — it boots with built-in mock content.

```bash
cp .env.example .env
docker compose up --build
# open http://localhost:8000   (look for the Blog + Notes sections)
```

Or without Docker:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Redis is optional locally; the cache degrades gracefully if it's absent.
```

`/healthz` reports `{"mock": true}` until real credentials are set.

## Wire up your real Notion

1. Create an internal integration at <https://www.notion.so/my-integrations>,
   copy the **Internal Integration Secret**.
2. Open your database in Notion → ••• → **Connections** → add the integration.
3. Copy the **database ID** from its URL
   (`notion.so/<workspace>/<DATABASE_ID>?v=...` — the 32-char chunk).
4. Put both in `.env`:
   ```env
   NOTION_TOKEN=secret_xxx
   NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Restart. `/healthz` now shows `{"mock": false}` and your real posts appear.

## Wire up the live webhook

1. Deploy so `/webhooks/notion` is reachable from the internet (see below).
2. In your integration settings → **Webhooks** → add a subscription pointing at
   `https://<your-domain>/webhooks/notion`.
3. Notion sends a one-off **verification token** — it's printed in the pod logs:
   ```bash
   kubectl -n blog logs deploy/blog-web | grep verification_token
   ```
   Copy it into `NOTION_WEBHOOK_SECRET` (Secret) and roll the deployment.
   Subsequent webhook calls are HMAC-verified; cache is wiped on each edit.

Without a webhook, edits still appear within `CACHE_TTL` seconds (default 3600).
Lower it if you prefer polling-style freshness over webhooks.

## Deploy to Kubernetes

```bash
# 1. Build & push the image to a registry your cluster can pull from.
docker build -t <registry>/blog-notion:latest .
docker push <registry>/blog-notion:latest
# set that image in k8s/deployment.yaml

# 2. Namespace + config
kubectl apply -f k8s/configmap.yaml      # creates the namespace via deployment.yaml too
kubectl apply -f k8s/deployment.yaml     # includes Namespace, Deployment, HPA

# 3. Secret (don't commit the filled-in version)
kubectl -n blog create secret generic blog-secrets \
  --from-literal=NOTION_TOKEN=secret_xxx \
  --from-literal=NOTION_DATABASE_ID=xxxx \
  --from-literal=NOTION_WEBHOOK_SECRET=xxxx

# 4. Redis, Service, Ingress
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml        # edit host + cluster-issuer first
```

Notes:
- **Redis is intentionally ephemeral** (no PVC). It's a cache — if it restarts,
  pages just re-fetch from Notion and re-populate. Nothing is lost.
- The web Deployment runs **non-root, read-only rootfs, all caps dropped**.
- An **HPA** scales the web tier 2→5 on CPU. Redis stays a singleton.

## Layout

```
app/
  main.py      routes, image proxy, webhook
  config.py    env settings
  notion.py    Notion API client (+ mock fallback)
  render.py    Notion blocks → HTML
  cache.py     Redis wrapper (degrades gracefully)
  mock.py      sample content for credential-free boot
  templates/   Jinja2
  static/      CSS
k8s/           manifests
Dockerfile / docker-compose.yml
```
