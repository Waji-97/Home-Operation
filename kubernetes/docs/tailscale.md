# Tailscale + KSOPS (encrypted GitOps secrets)

Tailscale is deployed as a **subnet router** to reach the home LAN
(`172.30.1.0/24`) from anywhere, with no public exposure. Its auth key is a secret,
and this repo is **public**, so it is committed **encrypted** with SOPS/age and
decrypted in-cluster by **KSOPS** at render time.

This page covers the one-time KSOPS wiring and how to bring up Tailscale.

## 1. Prerequisites (local)

On a machine that has the age **private** key (public key is in `.sops.yaml`):

```bash
brew install sops age              # macOS; or use your distro's packages
ls ~/.config/sops/age/keys.txt     # the private key must be here
```

If the key only exists on another host, copy it to
`~/.config/sops/age/keys.txt` (keep it off Git — `.gitignore` excludes `keys.txt`).

## 2. Wire KSOPS into argocd-repo-server (once)

```bash
# Give repo-server the age private key
kubectl create secret generic sops-age -n argocd \
  --from-file=keys.txt=$HOME/.config/sops/age/keys.txt

# Install the KSOPS plugin + enable the build flags
kubectl patch deploy argocd-repo-server -n argocd --patch-file \
  kubernetes/bootstrap/in-cluster/argocd-repo-server-ksops-patch.yaml
kubectl patch cm argocd-cm -n argocd --type=merge --patch-file \
  kubernetes/bootstrap/in-cluster/argocd-cm-patch.yaml

# Roll repo-server so the changes take effect
kubectl rollout restart deploy argocd-repo-server -n argocd
kubectl rollout status  deploy argocd-repo-server -n argocd
```

Verify existing apps still render after the restart:
```bash
kubectl get applications -n argocd   # homelab-root + longhorn still Synced/Healthy
```

## 3. Provide the Tailscale auth key

Create a key in the [admin console](https://login.tailscale.com/admin/settings/keys)
(reusable; tag it e.g. `tag:k8s`). Put it in the secret and encrypt:

```bash
# edit the placeholder, replace TS_AUTHKEY with the real key
$EDITOR kubernetes/apps/tailscale/secret.sops.yaml
sops -e -i kubernetes/apps/tailscale/secret.sops.yaml   # encrypts in place

git add kubernetes/apps/tailscale/secret.sops.yaml
git commit -m "feat(tailscale): add encrypted auth key"
git push
```

> Only the **encrypted** file is committed. Verify before pushing:
> `grep -q ENC kubernetes/apps/tailscale/secret.sops.yaml && echo encrypted`

## 4. Let it sync & approve the route

`homelab-root` picks up the `tailscale` child app automatically. Then in the
admin console:
1. **Approve** the advertised route `172.30.1.0/24` (Machines → node → Subnets).
2. **Disable key expiry** for the node.

## Verify

```bash
kubectl get applications -n argocd                 # tailscale Synced/Healthy
kubectl logs deploy/tailscale -n tailscale         # "Startup complete", authed
kubectl get secret -n tailscale                    # tailscale-auth + tailscale-state
# From a remote Tailscale client (after route approval):
ping 172.30.1.90                                   # reach the cp node over the tailnet
```

## Rollback (if repo-server breaks)

```bash
kubectl rollout undo deploy/argocd-repo-server -n argocd
```
