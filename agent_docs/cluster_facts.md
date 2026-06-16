# Cluster facts & constraints

| | |
|---|---|
| Nodes | `cp` (control-plane), `wk1`, `wk2` — **single control plane** |
| Kubernetes | v1.35.4 (Kubespray), CNI Calico |
| ArgoCD | v2.14.5, app-of-apps; local cluster = `in-cluster` |
| Storage | `longhorn` (default StorageClass) — use it for PVCs |
| Service CIDR | `10.96.0.0/18` |
| Pod CIDR | `192.168.0.0/16` |
| LAN | `172.30.1.0/24` (cp .90, wk1 .91, wk2 .92) |
| Ingress | **none yet** — expose via `NodePort`; LAN reachable remotely over Tailscale |
| Remote access | Tailscale subnet router (`apps/tailscale`) advertises the LAN |

## Tooling available on the Mac

`kubectl`, `helm` (3.x), `sops`, `age`, `kustomize`, `kubeconform`, `kube-linter`,
`gh` (authenticated). Use `gh` for GitHub API (unauth `curl` rate-limits at 60/hr).

## Implications for manifests

- Single control plane → no HA assumptions; single-replica workloads are fine.
- No ingress controller → don't write `Ingress` resources expecting them to work;
  use `Service` (`NodePort` for external).
- Small 3-node homelab → keep resource requests modest.
