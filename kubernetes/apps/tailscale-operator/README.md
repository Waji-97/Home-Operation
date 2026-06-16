# Tailscale Operator

The [Tailscale Kubernetes Operator](https://tailscale.com/kb/1236/kubernetes-operator)
— provides the `tailscale` `IngressClass` so apps can be exposed on the tailnet or
publicly via **Funnel** with a simple `Ingress` (see `apps/blog-notion`).

| | |
|---|---|
| Chart | `tailscale-operator` |
| Repo | https://pkgs.tailscale.com/helmcharts |
| Version | `1.98.4` |
| Namespace | `tailscale-system` |
| Auth | Secret `operator-oauth` (KSOPS) — OAuth client `client_id`/`client_secret` |

Distinct from `apps/tailscale` (the standalone **subnet router** in ns `tailscale`).

## One-time tailnet setup

1. Admin console → **Settings → OAuth clients** → create a client; grant it tag
   `tag:k8s`. Put the id/secret into `secret.sops.yaml`, then
   `sops --config kubernetes/.sops.yaml -e -i secret.sops.yaml`.
2. ACL: define `tag:k8s` owners, and **enable Funnel** for it via `nodeAttrs`:
   ```jsonc
   "nodeAttrs": [{ "target": ["tag:k8s"], "attr": ["funnel"] }]
   ```

Until valid OAuth creds are set, the operator pod will crash-loop (harmless; no
other app is affected).
