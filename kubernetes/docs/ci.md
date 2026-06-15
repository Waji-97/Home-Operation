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
| **Policy (kube-linter)** | Runs [`scripts/policy-check.sh`](../../scripts/policy-check.sh): [kube-linter](https://github.com/stackrox/kube-linter) security/config checks on first-party manifests (upstream Helm charts are skipped). Config: [`.kube-linter.yaml`](../../.kube-linter.yaml). |

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

## Policy exceptions

kube-linter runs its default check set. Accepted exceptions are recorded per
resource as `ignore-check.kube-linter.io/<check>` annotations (see the tailscale
Deployment), so each check stays enforced for every other workload. Tighten policy
by opting into stricter non-default checks in `.kube-linter.yaml`.

## Renovate (dependency updates)

[`renovate.json`](../../renovate.json) configures [Renovate](https://docs.renovatebot.com)
to open PRs for:

- **Helm charts** — the `version:` in each app's `helmCharts:` block (e.g. Longhorn),
  via Renovate's kustomize manager.
- **Container images** — image tags in `kubernetes/apps/**` (e.g. tailscale), via
  the kubernetes manager.

Update PRs run through the CI above before merge. Minor/patch bumps are grouped per
dependency and PRs are labelled `dependencies`; a Dependency Dashboard issue tracks
everything. Runs are scheduled weekly.

**Setup (one-time):** install the [Mend Renovate app](https://github.com/apps/renovate)
on the `Waji-97/Home-Operation` repo (free for public repos). It picks up
`renovate.json` automatically and opens an onboarding PR.

## Roadmap

- Harden tailscale (non-root, read-only root fs) to drop the kube-linter exceptions.
- `kyverno`/`gatekeeper` admission policies in-cluster.
