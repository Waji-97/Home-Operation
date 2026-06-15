# Home-Operation

[![CI](https://github.com/Waji-97/Home-Operation/actions/workflows/ci.yml/badge.svg)](https://github.com/Waji-97/Home-Operation/actions/workflows/ci.yml)

In-house Kubernetes cluster for home operations, managed end-to-end with **GitOps**
(ArgoCD, app-of-apps pattern). Everything in this repo is the source of truth for
the cluster — changes are made via Git, and ArgoCD reconciles them.

## Cluster

3× mini-PC nodes provisioned with [Kubespray](kubernetes/docs/initial-setup.md).

| Node | Role          | LAN IP        |
|------|---------------|---------------|
| `cp` | control-plane | 172.30.1.90   |
| `wk1`| worker        | 172.30.1.91   |
| `wk2`| worker        | 172.30.1.92   |

| | |
|---|---|
| Kubernetes | v1.35.4 (Kubespray) |
| CNI | Calico |
| Service CIDR | `10.96.0.0/18` |
| Pod CIDR | `192.168.0.0/16` |
| GitOps | ArgoCD (app-of-apps) |
| Storage | Longhorn (default StorageClass) |

## GitOps layout

```
kubernetes/
├── bootstrap/in-cluster/   # root app-of-apps + one-time argocd-cm patch
├── clusters/in-cluster/    # child Applications the root app watches
├── apps/                   # the actual workload manifests (Helm via Kustomize)
├── docs/                   # setup & architecture docs
└── kubespray/              # cluster provisioning inventory & vars
```

The root `Application` (`homelab-root`) is the only thing applied by hand; it then
deploys every child app. See **[GitOps structure](kubernetes/docs/gitops-structure.md)**
for the full flow and how to add a new app.

## Applications

| App | Purpose | Docs |
|-----|---------|------|
| Longhorn | Distributed block storage (default StorageClass) | [README](kubernetes/apps/longhorn/README.md) |
| Tailscale | Subnet router — remote access to the home LAN | [README](kubernetes/apps/tailscale/README.md) · [setup](kubernetes/docs/tailscale.md) |

## Documentation

- [Initial setup (Kubespray)](kubernetes/docs/initial-setup.md)
- [ArgoCD bootstrap](kubernetes/docs/argocd.md)
- [GitOps structure](kubernetes/docs/gitops-structure.md)
- [CI (GitHub Actions)](kubernetes/docs/ci.md)

## Roadmap

- [x] ArgoCD app-of-apps bootstrap
- [x] Longhorn storage under GitOps
- [x] In-cluster secret decryption (SOPS/age via KSOPS)
- [x] Tailscale (remote access to the home network)
- [x] GitHub Actions (manifest validation on PRs)
- [x] Renovate (automated chart + image bumps)
- [x] kube-linter policy checks
