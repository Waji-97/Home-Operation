# CI (GitHub Actions)

[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) runs on every pull
request and on pushes to `main` that touch `kubernetes/**` or `scripts/**`. It
catches manifest problems before ArgoCD tries to sync them.

## Jobs

| Job | What it does |
|-----|--------------|
| **Secret scan** | [gitleaks](https://github.com/gitleaks/gitleaks) scans for committed secrets. Encrypted `*.sops.yaml` files and the age public key are allow-listed in [`.gitleaks.toml`](../../.gitleaks.toml). |
| **YAML lint** | `yamllint` with a relaxed config ([`.yamllint.yaml`](../../.yamllint.yaml)); skips vendored charts and encrypted secrets. |
| **Render & validate** | Runs [`scripts/validate-manifests.sh`](../../scripts/validate-manifests.sh): renders each kustomization (`kustomize build --enable-helm`) and schema-checks it with [kubeconform](https://github.com/yannh/kubeconform). |

## The validation script

`scripts/validate-manifests.sh` is the source of truth and is runnable locally:

```bash
# prerequisites: kustomize, kubeconform, helm
./scripts/validate-manifests.sh
```

It performs three checks:

1. **Encrypted secrets** — every `*.sops.yaml` (except the `.sops.yaml` config)
   must contain `ENC[...]`. A plaintext secret fails the build.
2. **Render + schema** — each kustomization is rendered and validated.
   `kubeconform` runs with `-ignore-missing-schemas`, so CRD-based resources
   (Longhorn CRs, ArgoCD `Application`s) are skipped rather than failed.
3. **Standalone manifests** — the bootstrap root `Application` parses.

## Why the age key is NOT in CI

KSOPS apps (e.g. `apps/tailscale`) need the age **private** key to render their
encrypted secret. We deliberately keep that key **out of GitHub** to minimise where
the master decryption key exists. Instead, CI validates those apps' **static**
resources (namespace, RBAC, Deployment) and confirms the secret is encrypted — it
does not decrypt. ArgoCD's repo-server is the only place that holds the key.

## Roadmap

- Renovate/Dependabot for chart + image version bumps.
- `kube-linter`/`kyverno` policy checks (security context, resource limits).
