# Container images & delivery

For Dockerized custom apps.

## Image conventions

- **Registry:** Docker Hub `docker.io/waji97/<app>` (public).
- **Pin tags** in the Deployment — no `:latest` (fails kube-linter; also non-reproducible).
  Renovate's kubernetes manager scans `kubernetes/apps/**` and opens bump PRs.
- Build a **small, non-root** image (set `USER`, prefer distroless/alpine) so the
  hardened Deployment template works (`runAsNonRoot: true`, `readOnlyRootFilesystem:
  true`, dropped caps). See [deploying_new.md](deploying_new.md).
- If the app writes to disk at runtime, mount an `emptyDir` (e.g. `/tmp`) rather than
  making the root filesystem writable.

## App-delivery CI/CD (FUTURE — not built yet)

A separate pipeline from the manifest-validation CI:

1. Build + push the image to `docker.io/waji97/<app>:<tag>`.
2. Bump the tag in `kubernetes/apps/<app>/deployment.yaml`.
3. ArgoCD deploys whatever the manifest in Git says.

Keep delivery **declarative**: the running version is always what the manifest in Git
declares. Do **not** `kubectl set image` by hand. Tag bumps go through Git (the
pipeline commits them, or Renovate proposes them).
