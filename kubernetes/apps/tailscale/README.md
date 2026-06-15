# Tailscale (subnet router)

Connects the home network to a [Tailscale](https://tailscale.com) tailnet so the
LAN is reachable from outside, without exposing anything publicly.

| | |
|---|---|
| Mode | Standalone subnet router, userspace networking |
| Advertises | `172.30.1.0/24` (home LAN) |
| Image | `tailscale/tailscale:v1.98.4` |
| Namespace | `tailscale` |
| State | Secret `tailscale-state` (in-cluster, auto-managed) |
| Auth | Secret `tailscale-auth` → encrypted `secret.sops.yaml` (KSOPS) |

## How the secret works

The auth key is committed **encrypted** (SOPS/age) because this repo is public.
`secret-generator.yaml` is a KSOPS generator that ArgoCD's repo-server decrypts at
render time. See [docs/tailscale.md](../../docs/tailscale.md) for the one-time
KSOPS wiring and how to provide the key.

## Rotating the auth key

```bash
sops kubernetes/apps/tailscale/secret.sops.yaml   # edit in place, decrypted in $EDITOR
git commit -am "chore(tailscale): rotate auth key" && git push
```
(The node keeps working off `tailscale-state` even after the auth key expires; the
key is only needed for initial registration / re-auth.)

## After first sync

In the Tailscale admin console:
1. **Approve** the advertised route `172.30.1.0/24` (Machines → this node → Subnets).
2. **Disable key expiry** for the node so it doesn't drop off.

## Switching to kernel networking (higher throughput)

Userspace mode is simplest (no node changes) but slower. For kernel mode: drop
`TS_USERSPACE`, add `securityContext.capabilities: [NET_ADMIN]`, and ensure
`net.ipv4.ip_forward=1` (+ `net.ipv6.conf.all.forwarding=1`) on the worker nodes.
