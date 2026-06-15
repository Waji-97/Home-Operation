# GitOps Structure (App-of-Apps)

This cluster is reconciled by **ArgoCD** using the **app-of-apps** pattern. All
desired cluster state lives in this Git repo; ArgoCD continuously syncs it.

## Directory layout

```
kubernetes/
├── bootstrap/
│   └── in-cluster/
│       ├── root.yaml              # the root Application (app-of-apps) — applied once
│       └── argocd-cm-patch.yaml   # one-time argocd-cm patch (enable Helm-via-Kustomize)
├── clusters/
│   └── in-cluster/                # what the root app watches
│       ├── kustomization.yaml     # lists every child Application
│       └── apps/
│           └── longhorn.yaml      # one child Application per workload
├── apps/
│   └── longhorn/                  # the actual manifests for each workload
│       ├── kustomization.yaml
│       ├── values.yaml
│       └── README.md
├── .sops.yaml                     # encrypt app secrets (age) — repo auth not needed (public repo)
├── docs/
└── kubespray/                     # cluster provisioning (not GitOps-managed)
```

`in-cluster` is ArgoCD's name for the local cluster (`https://kubernetes.default.svc`).
Keeping a per-cluster directory makes the layout multi-cluster-ready.

## How it flows

```
root.yaml (homelab-root)
   └── watches  clusters/in-cluster/   (kustomize)
         └── renders child Applications: apps/longhorn.yaml, ...
               └── each points at  apps/<name>/   (kustomize + Helm)
                     └── actual Kubernetes resources
```

1. `homelab-root` is the only Application applied by hand. It auto-syncs.
2. It renders the child `Application` manifests listed in
   `clusters/in-cluster/kustomization.yaml`.
3. Each child Application deploys the manifests under `apps/<name>/`.

## Adding a new app

1. Create `apps/<name>/` with a `kustomization.yaml` (plain manifests, or a
   `helmCharts:` block for an upstream chart) and a `README.md`.
2. Create `clusters/in-cluster/apps/<name>.yaml` — an ArgoCD `Application`
   pointing at `kubernetes/apps/<name>` (copy `longhorn.yaml` as a template).
3. Add `apps/<name>.yaml` to `clusters/in-cluster/kustomization.yaml`.
4. Commit & push. `homelab-root` picks it up automatically.

## Helm via Kustomize

Upstream Helm charts are rendered through Kustomize's `helmCharts:` field. This
needs `kustomize.buildOptions: --enable-helm` on the `argocd-cm` ConfigMap — see
`bootstrap/in-cluster/argocd-cm-patch.yaml` (applied once during bootstrap).

## Secrets (SOPS / age)

The repo is **public**, so ArgoCD needs no credentials to read it. SOPS+age
(`.sops.yaml`) is only for encrypting **application** secrets committed to Git.

- Encrypt: `sops -e -i apps/<name>/secret.sops.yaml`
- The age **public** key is the recipient in `.sops.yaml`; the **private** key
  (`~/.config/sops/age/keys.txt`) stays off-repo.
- **TODO (later):** wire in-cluster decryption (KSOPS sidecar on
  `argocd-repo-server`) so ArgoCD can decrypt `*.sops.yaml` at render time.

## Bootstrapping a fresh cluster

See [argocd.md](argocd.md) for the exact bootstrap + Longhorn adoption steps.
