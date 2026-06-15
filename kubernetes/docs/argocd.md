# ArgoCD Setup
ArgoCD is installed by default as ArgoCD is enabled in the kubespray custom variable file.

```bash
➜ k get po -n argocd
NAME                                                READY   STATUS    RESTARTS      AGE
argocd-application-controller-0                     1/1     Running   1 (58m ago)   10d
argocd-applicationset-controller-5cc599989f-l9s4t   1/1     Running   1 (58m ago)   10d
argocd-dex-server-6bd7bd9c68-xbzbs                  1/1     Running   1 (58m ago)   10d
argocd-notifications-controller-658879594b-nncn9    1/1     Running   1 (58m ago)   10d
argocd-redis-6d96789db9-tlmsw                       1/1     Running   1 (58m ago)   10d
argocd-repo-server-579b78689-gnxgn                  1/1     Running   1 (58m ago)   10d
argocd-server-574588fc44-cwxcl                      1/1     Running   1 (58m ago)   10d
```

<br>

To access the ArgoCD Web UI, we can patch the argocd-server service to be `NodePort`
```bash
➜ kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
```

<br>

> This step requires `argocd cli` to be installed beforehand. Install argocd cli from the official argocd github releases page.

Initial Admin password for argocd server can be found using the following command
```bash
➜ argocd admin initial-password -n argocd
```

### Connect HomeLab Github repo with ArgoCD
The `Home-Operation` repository is **public**, so ArgoCD reads it without any
credentials — no repo `Secret` is required. The Applications simply reference
`repoURL: https://github.com/Waji-97/Home-Operation`.

> SOPS + age are still used in this repo, but only to encrypt **application**
> secrets committed to Git (e.g. DB passwords) — not for repo auth. See
> [gitops-structure.md](gitops-structure.md#secrets-sops--age). In-cluster
> decryption (KSOPS) is a later task.

<br>

### Patch ArgoCD ConfigMap
The following one-time patch is required to:
- Enable Helm templating using Kustomize (`--enable-helm`)
- Enable App-of-Apps health check for the `Application` custom resource

```bash
➜ kubectl patch cm argocd-cm -n argocd --type=merge \
    --patch-file kubernetes/bootstrap/in-cluster/argocd-cm-patch.yaml
configmap/argocd-cm patched
```


### Create Root Application for App-of-Apps
Deploy the root application for the in-cluster (local) cluster. This is the only
Application applied by hand; it then renders every child Application.
```bash
➜ kubectl apply -f kubernetes/bootstrap/in-cluster/root.yaml
application.argoproj.io/homelab-root created
```

See [gitops-structure.md](gitops-structure.md) for the full directory layout and
how the app-of-apps fan-out works.

<br>

### Adopt the existing Longhorn install (one-time)
Longhorn was first installed manually via Helm. The `longhorn` Application pins the
**same chart version and values**, so ArgoCD adopts the running install instead of
reinstalling it. It ships **without** automated sync so the first sync can be
reviewed.

```bash
# 1. Review the diff — expect only ownership metadata, no destructive changes
➜ argocd app diff longhorn

# 2. Adopt via server-side apply
➜ argocd app sync longhorn --server-side

# 3. Verify nothing was disturbed
➜ kubectl get pods -n longhorn-system
➜ kubectl get sc                       # longhorn still (default)
➜ kubectl get volumes.longhorn.io -A   # existing volumes healthy
➜ kubectl get pvc -A                   # existing PVCs still Bound
```

> Do **not** run `helm uninstall longhorn` — ArgoCD now owns these resources. The
> original Helm release secret remains but is inert.

Once verified, enable continuous reconciliation by adding `automated` to
`kubernetes/clusters/in-cluster/apps/longhorn.yaml`:
```yaml
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```
Then commit & push — `homelab-root` applies the change.