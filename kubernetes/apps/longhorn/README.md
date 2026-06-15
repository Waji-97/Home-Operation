# Longhorn

Distributed block storage for the cluster. Provides the default `StorageClass`
(`longhorn`) backing all PersistentVolumeClaims.

| | |
|---|---|
| Chart | `longhorn` |
| Repo | https://charts.longhorn.io |
| Version | `1.12.0` (appVersion `v1.12.0`) |
| Namespace | `longhorn-system` |

## Notes

- This app **adopts** an install that originally came from a manual
  `helm install`. The chart version and `values.yaml` are pinned to exactly match
  that release so adoption does not disturb existing volumes.
- Rendered via Kustomize's `helmCharts` field, so `argocd-cm` must have
  `kustomize.buildOptions: --enable-helm`.
- Do **not** run `helm uninstall longhorn` — ArgoCD now owns these resources and
  an uninstall would delete them. The original Helm release secret is inert.

## Upgrading

1. Bump `version` in `kustomization.yaml`.
2. Diff against the running state: `argocd app diff longhorn`.
3. Commit; ArgoCD syncs automatically.
