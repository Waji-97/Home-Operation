# blog-notion

Personal blog/notes site — **FastAPI + Jinja2**, Notion as a headless CMS, **Redis**
cache, Notion **webhook** for instant publish. App source lives in
[`applications/blog-notion/`](../../../applications/blog-notion/); this dir is the
GitOps deployment.

| | |
|---|---|
| Image | `docker.io/waji97/blog-notion:<tag>` (built from `applications/blog-notion`) |
| Namespace | `blog` |
| Port | 8000 (Service `blog-web` :80 → :8000) |
| Cache | `redis` (in-memory, no PVC — ephemeral by design) |
| Public access | Tailscale **Funnel** Ingress → `https://blog.<tailnet>.ts.net` |
| Config | ConfigMap `blog-config` (non-secret) |
| Secrets | `blog-secrets` (KSOPS): `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `NOTION_WEBHOOK_SECRET` |

## Notes

- No HPA (cluster has no metrics-server) — fixed `replicas: 2`.
- Requires `apps/tailscale-operator` (provides the `tailscale` IngressClass for Funnel).
- Webhook URL for Notion: `https://blog.<tailnet>.ts.net/webhooks/notion`. After the
  first handshake, read the verification token from the pod logs
  (`kubectl -n blog logs deploy/blog-web | grep verification_token`), put it in
  `NOTION_WEBHOOK_SECRET`, re-encrypt `secret.sops.yaml`, push.
- Image bumps: build from `applications/blog-notion`, push, update the tag here
  (a build/push CI pipeline will automate this — see `agent_docs/images.md`).
