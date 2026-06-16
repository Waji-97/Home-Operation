# CI & policy

Author manifests so they pass these before merge. Run locally:
```bash
./scripts/validate-manifests.sh
./scripts/policy-check.sh
```

## What CI enforces ([.github/workflows/ci.yml](../.github/workflows/ci.yml))

- **`scripts/validate-manifests.sh`** — every `*.sops.yaml` is encrypted; every
  kustomization renders (`kustomize build --enable-helm`, `--helm-kube-version
  1.35.0`) and passes kubeconform (`-ignore-missing-schemas`, so CRD-based resources
  like ArgoCD `Application`s and Longhorn CRs are skipped, not failed).
- **`scripts/policy-check.sh`** — kube-linter default checks on **first-party** apps
  (apps with `helmCharts:` are skipped — we don't author upstream charts). Config:
  [`.kube-linter.yaml`](../.kube-linter.yaml).
- **gitleaks** secret scan + relaxed **yamllint**.

## Pipeline pins (don't drift)

kustomize `v5.4.3`, kubeconform `v0.6.7`, kube-linter `v0.8.3`, Helm **3.x**
(currently `v3.21.1`). **Helm 4 breaks `kustomize --enable-helm`** — renovate.json
has `allowedVersions: "<4.0.0"` for `helm` so it's never proposed. Don't undo this.

## kube-linter exceptions

Use **per-resource** annotations, never repo-wide disables:
```yaml
metadata:
  annotations:
    ignore-check.kube-linter.io/<check>: "why this is acceptable"
```
This keeps the check enforced for every other workload. The hardened Deployment in
[deploying_new.md](deploying_new.md) passes the default set with no exceptions —
prefer fixing the manifest over adding an annotation.

## Renovate

Configured in [renovate.json](../renovate.json): bumps the Longhorn chart, app image
tags (`kubernetes/apps/**`), GitHub Actions, and the kubespray release (reminder
only). Weekly schedule; Dependency Dashboard = GitHub issue #1.
Human-facing detail: [kubernetes/docs/ci.md](../kubernetes/docs/ci.md).
