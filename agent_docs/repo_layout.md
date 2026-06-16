# Repo layout & app-of-apps flow

```
kubernetes/
├── bootstrap/in-cluster/     # applied by hand ONCE (root app + argocd-cm/repo-server patches)
├── clusters/in-cluster/      # the root app watches this; lists child Applications
│   ├── kustomization.yaml    #   -> add new apps here
│   └── apps/<name>.yaml       #   -> one child Application per app
├── apps/<name>/              # the actual workload manifests (THIS is where apps live)
├── docs/                     # architecture & runbooks (human-facing)
└── kubespray/                # cluster provisioning (NOT GitOps-managed)
.sops.yaml                    # at kubernetes/.sops.yaml — SOPS age recipient
.github/workflows/ci.yml      # manifest validation pipeline
scripts/                      # validate-manifests.sh, policy-check.sh
renovate.json                 # dependency bumps
CLAUDE.md                     # index + hard rules
agent_docs/                   # detailed playbooks (this dir)
```

## Flow

```
bootstrap/in-cluster/root.yaml   (homelab-root, applied once)
  └─ watches clusters/in-cluster/  (kustomize)
       └─ renders child Applications: clusters/in-cluster/apps/*.yaml
            └─ each points at apps/<name>/  (kustomize, + Helm/KSOPS as needed)
                 └─ actual Kubernetes resources
```

- `homelab-root` is the only Application applied by hand; it deploys all child apps.
- Adding an app = create `apps/<name>/` + a child Application + list it in
  `clusters/in-cluster/kustomization.yaml`. See [deploying_new.md](deploying_new.md).
- `in-cluster` = ArgoCD's name for the local cluster (`https://kubernetes.default.svc`);
  the per-cluster dir keeps it multi-cluster-ready.

Human-facing version: [kubernetes/docs/gitops-structure.md](../kubernetes/docs/gitops-structure.md).
