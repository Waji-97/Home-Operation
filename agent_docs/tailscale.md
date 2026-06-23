# Tailscale (subnet router + operator/Funnel)

Two **independent** Tailscale deployments live in this repo — don't conflate them:

| App | Namespace | Purpose |
|-----|-----------|---------|
| [`tailscale`](../kubernetes/apps/tailscale/) | `tailscale` | **Subnet router** — advertises the LAN `172.30.1.0/24` so you can reach nodes/services from outside. Standalone pod + auth key. |
| [`tailscale-operator`](../kubernetes/apps/tailscale-operator/) | `tailscale-system` | **Kubernetes Operator** — registers the `tailscale` IngressClass and exposes apps publicly via **Funnel** (`https://<host>.<tailnet>.ts.net`). Used by `blog-notion`. |

This doc covers the **operator + Funnel** path (OAuth, ACL, exposing an app). The
subnet router just needs a tagged auth key in its KSOPS secret.

---

## How the operator authenticates

The chart ([kustomization.yaml](../kubernetes/apps/tailscale-operator/kustomization.yaml),
pinned `tailscale-operator` **v1.98.4** from `https://pkgs.tailscale.com/helmcharts`)
reads a Secret **`operator-oauth`** (keys `client_id` / `client_secret`) in
`tailscale-system`. We provide it KSOPS-encrypted
([secret.sops.yaml](../kubernetes/apps/tailscale-operator/secret.sops.yaml) +
`secret-generator.yaml`). The operator uses those OAuth credentials to mint
Tailscale auth keys for itself and for the per-Ingress proxy pods.

### One-time tailnet setup (user-side, admin console)

These steps are **not** in Git — they're tailnet config. Do them once.

1. **OAuth client** — Settings → **OAuth clients**
   (https://login.tailscale.com/admin/settings/oauth) → *Generate*:
   - Scopes: **Devices › Core = Write** and **Auth Keys = Write**.
   - Tag: **`tag:k8s`** (requires the `tagOwners` entry below).
   - Copy the **client id + secret** into `operator-oauth` (encrypt with SOPS — see
     [secrets.md](secrets.md); never paste plaintext into the repo).
2. **ACL policy** — Access controls (https://login.tailscale.com/admin/acls). This
   tailnet uses the **`grants`** model. The policy file is **one HuJSON object** —
   add `tagOwners` + `nodeAttrs` as top-level keys (don't paste a second `{ }`):

   ```jsonc
   {
   	"grants": [
   		{ "src": ["*"], "dst": ["*"], "ip": ["*"] },
   	],

   	"tagOwners": {
   		"tag:k8s":          ["autogroup:admin"],
   		"tag:k8s-operator": ["tag:k8s"],   // operator tags its OWN device tag:k8s-operator;
   	},                                     // the tag:k8s OAuth client must own it to mint that key

   	"nodeAttrs": [
   		{ "target": ["tag:k8s"], "attr": ["funnel"] },  // allow Funnel on proxy devices (tag:k8s)
   	],

   	"ssh": [
   		{ "action": "check", "src": ["autogroup:member"], "dst": ["autogroup:self"], "users": ["autogroup:nonroot", "root"] },
   	],
   }
   ```
3. **Enable HTTPS** — DNS (https://login.tailscale.com/admin/dns): **MagicDNS** on
   **and** **HTTPS Certificates** enabled. Funnel can't get a TLS cert without this.

---

## Exposing an app via Funnel

Add an `Ingress` to the app (see [blog-notion ingress](../kubernetes/apps/blog-notion/ingress.yaml)):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <app>
  namespace: <ns>
  annotations:
    tailscale.com/funnel: "true"      # public internet. Omit for tailnet-only access.
spec:
  ingressClassName: tailscale
  defaultBackend:
    service: { name: <svc>, port: { number: 80 } }
  tls:
    - hosts: ["<host>"]               # becomes https://<host>.<tailnet>.ts.net
```

- Public URL = `https://<host>.<tailnet>.ts.net` (our tailnet: `tail33529a.ts.net`,
  so blog = `https://blog.tail33529a.ts.net`).
- The operator spins up a `ts-<app>-*` proxy pod in `tailscale-system` per Ingress.
- The child Application **must** carry `ServerSideApply=true` **and**
  `argocd.argoproj.io/compare-options: ServerSideDiff=true` — the operator ships CRDs
  and k8s 1.35 adds `.status.terminatingReplicas`, which trips ArgoCD's bundled schema
  otherwise (same fix as longhorn). See
  [tailscale-operator child app](../kubernetes/clusters/in-cluster/apps/tailscale-operator.yaml).

---

## Troubleshooting (errors we actually hit)

| Symptom (operator logs / Ingress events) | Cause | Fix |
|------|-------|-----|
| `401 Unauthorized … API token invalid` | `operator-oauth` still `REPLACE_ME`, or wrong creds | Put real OAuth id/secret in the secret, re-encrypt, sync |
| `requested tags [tag:k8s-operator] are invalid or not permitted (400)` | OAuth client tagged `tag:k8s` can't mint the operator's own `tag:k8s-operator` key | Add `"tag:k8s-operator": ["tag:k8s"]` to `tagOwners` |
| Ingress event `HTTPSNotEnabled` / no URL appears | HTTPS certs not enabled on tailnet | Enable MagicDNS + HTTPS Certificates (DNS page) |
| ArgoCD `ComparisonError … .status.terminatingReplicas: field not declared in schema` | SSA structured-merge diff vs k8s 1.35 schema | `ServerSideDiff=true` on the child Application |
| `policy requires hardware attestation … device does not support it` (proxy log) | Benign — proxy noting no TPM | Ignore |

After changing OAuth/ACL, restart the operator to retry fast:
`kubectl -n tailscale-system rollout restart deploy/operator`.

**Verify:** Ingress gets a URL (`kubectl -n blog get ingress blog -o
jsonpath='{.status.loadBalancer.ingress}'`), then `curl https://<host>.<tailnet>.ts.net/healthz`
from off-network.

---

## Security

- **Funnel = public internet.** Only Funnel apps that are meant to be public and have
  their own auth (the blog is public; `/webhooks/notion` is HMAC-verified). Never
  Funnel a dashboard/admin/DB.
- Treat any auth key or OAuth secret pasted into chat/logs as **compromised** —
  revoke and rotate. Only the SOPS-encrypted form belongs in this public repo.
- See [secrets.md](secrets.md) for the KSOPS encrypt/commit flow.
