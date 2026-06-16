# CLAUDE.md — Home-Operation

GitOps state for a 3-node home Kubernetes cluster, reconciled by ArgoCD
(app-of-apps). **Public repo.** This file = hard rules + index; full detail per topic
is in [`agent_docs/`](agent_docs/).

## Rules (MUST / MUST NOT) — one line each

- NEVER commit a plaintext secret; encrypt with SOPS/age as `*.sops.yaml`. → [secrets](agent_docs/secrets.md)
- One app = one dir `kubernetes/apps/<name>/`, wired via a child Application. → [deploying_new](agent_docs/deploying_new.md)
- Never apply manifests by hand — everything is GitOps; ArgoCD applies it.
- Pin every image and chart version; no `:latest`. → [images](agent_docs/images.md)
- Manifests MUST pass `./scripts/validate-manifests.sh` + `./scripts/policy-check.sh`. → [ci_policy](agent_docs/ci_policy.md)
- Helm stays on 3.x in CI (Helm 4 breaks `kustomize --enable-helm`); don't change the pin.
- kube-linter exceptions = per-resource `ignore-check.kube-linter.io/<check>` annotations, never repo-wide.
- No ingress controller — expose via `Service` NodePort, not `Ingress`. → [cluster_facts](agent_docs/cluster_facts.md)
- Use the `longhorn` default StorageClass for PVCs.
- Commits use Conventional Commits; push to `main` only when the user asks.
- Don't restructure the repo layout / app-of-apps wiring without asking. → [repo_layout](agent_docs/repo_layout.md)

## Where to look — [agent_docs/](agent_docs/)

| Task | Doc |
|------|-----|
| Repo layout & app-of-apps flow | [repo_layout.md](agent_docs/repo_layout.md) |
| Deploy a new app (all manifest templates) | [deploying_new.md](agent_docs/deploying_new.md) |
| Secrets (SOPS / KSOPS) | [secrets.md](agent_docs/secrets.md) |
| Container images & delivery | [images.md](agent_docs/images.md) |
| CI & policy (kube-linter, Renovate) | [ci_policy.md](agent_docs/ci_policy.md) |
| Cluster facts & constraints | [cluster_facts.md](agent_docs/cluster_facts.md) |

Human-facing docs: [kubernetes/docs/](kubernetes/docs/).
