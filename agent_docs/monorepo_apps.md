# Monorepo: custom app source + build/push

This repo is a **monorepo** for first-party apps: it holds both the app's **source
code** and its **GitOps manifests**, kept in separate trees. `blog-notion` is the
reference example.

## Layout

```
applications/<app>/            # SOURCE — built into an image. NOT deployed by ArgoCD.
├── Dockerfile                 #   small, non-root (USER), single port, /healthz
├── app/ …                     #   application code
├── requirements.txt           #   (or package.json, go.mod, …)
└── README.md, docker-compose.yml

kubernetes/apps/<app>/         # MANIFESTS — what ArgoCD actually deploys (our rules)
├── namespace.yaml  deployment.yaml  service.yaml  configmap.yaml
├── ingress.yaml               #   Tailscale Funnel, if public — see tailscale.md
├── secret.sops.yaml  secret-generator.yaml   # KSOPS — see secrets.md
└── kustomization.yaml

kubernetes/clusters/in-cluster/apps/<app>.yaml   # child Application (wires it in)
```

- **`applications/`** = source only. ArgoCD never looks here; it's the input to the
  image build. The app's *own* `k8s/` manifests (if it ships any) are **not** copied —
  we re-author manifests under `kubernetes/apps/<app>/` to match repo conventions
  (see [deploying_new.md](deploying_new.md)).
- **`kubernetes/apps/<app>/`** = the deployable manifests, wired into app-of-apps
  exactly like any other app (see [repo_layout.md](repo_layout.md)).
- The two are linked only by the **pinned image tag** in `deployment.yaml`.

### What must NOT be copied into `applications/<app>/`
`.env` / any real secrets (the repo is public — creds go through KSOPS instead),
`.git`, `.venv`, `.DS_Store`, and the app's stock `k8s/`. Confirm `.env` is
gitignored before committing.

## Build & push the image

Registry is `docker.io/waji97/<app>` (public) — see [images.md](images.md). The Mac
is **arm64**, the cluster nodes are **amd64**, so always cross-build:

```bash
docker login -u waji97
docker buildx build --platform linux/amd64 \
  -t docker.io/waji97/<app>:<tag> applications/<app> --push
```

Then **pin that tag** in `kubernetes/apps/<app>/deployment.yaml` (never `:latest`)
and commit. ArgoCD runs whatever the manifest in Git declares — don't
`kubectl set image` by hand. The image must exist in the registry **before** ArgoCD
syncs the Deployment (else `ImagePullBackOff`).

## Build/push CI/CD (Phase 2 — not built yet)

A pipeline separate from the manifest-validation CI, triggered on
`applications/<app>/**`:

1. `docker buildx` → push `docker.io/waji97/<app>:<tag>` (needs repo secrets
   `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN`).
2. Bump the tag in `kubernetes/apps/<app>/deployment.yaml` and commit.
3. ArgoCD redeploys from Git.

Keep it **declarative** — the running version is always what Git says. Detail lands
in [images.md](images.md) when built.

## Checklist for a new custom app

1. Copy source → `applications/<app>/` (exclude the list above).
2. Author manifests → `kubernetes/apps/<app>/` per [deploying_new.md](deploying_new.md).
3. Secrets via KSOPS → [secrets.md](secrets.md). Public exposure via Funnel →
   [tailscale.md](tailscale.md).
4. Child Application + list in `clusters/in-cluster/kustomization.yaml`.
5. Build & push the image; pin the tag.
6. `./scripts/validate-manifests.sh` && `./scripts/policy-check.sh`, then commit.
