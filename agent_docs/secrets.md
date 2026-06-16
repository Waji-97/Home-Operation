# Secrets (SOPS + age + KSOPS)

This is a **public** repo — secrets are committed **only** as SOPS-encrypted
`*.sops.yaml` files. In-cluster decryption is wired (KSOPS on argocd-repo-server),
so ArgoCD decrypts them at render time.

## Add a secret to an app

1. Create `kubernetes/apps/<name>/secret.sops.yaml` (plaintext while editing —
   **do not commit it yet**):
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: <name>-secret
     namespace: <name>
   type: Opaque
   stringData:
     SOME_KEY: <value>
   ```
2. Create `kubernetes/apps/<name>/secret-generator.yaml`:
   ```yaml
   apiVersion: viaduct.ai/v1
   kind: ksops
   metadata:
     name: <name>-secret-generator
     annotations:
       config.kubernetes.io/function: |
         exec:
           path: ksops
   files:
     - ./secret.sops.yaml
   ```
3. Add `generators: [./secret-generator.yaml]` to the app's `kustomization.yaml`.
4. Reference the secret in the workload (`secretKeyRef` / `envFrom` / volume).
5. **Encrypt before committing** (only the encrypted file is ever committed):
   ```bash
   sops --config kubernetes/.sops.yaml -e -i kubernetes/apps/<name>/secret.sops.yaml
   grep -q 'ENC\[AES256' kubernetes/apps/<name>/secret.sops.yaml && echo encrypted
   ```

## Key facts

- `.sops.yaml` (at `kubernetes/.sops.yaml`) encrypts only `data`/`stringData` of
  files matching `*.sops.yaml`.
- **age recipient (public key, safe to share):**
  `age14y3vjfm4dfz6pr9fz7ndclpa24avmk9ewn3eadfh2fylmnenkp8qqygz4h`
- The **private** key lives at `~/.config/sops/age/keys.txt` (off-repo) and in the
  cluster as Secret `sops-age` in ns `argocd`. Never commit it.
- **If the building session lacks the private key / `sops`** (scaffolding on another
  machine/repo): write `secret.sops.yaml` as a plaintext placeholder, leave it
  **uncommitted**, and run the `sops -e -i` step later in the main Home-Operation
  session (this Mac has the key). Generator + wiring can be done anywhere.
- If an env var NAME contains `SECRET`/`TOKEN` but the value is harmless (e.g. a
  Secret *name*), suppress the kube-linter false positive with
  `ignore-check.kube-linter.io/env-var-secret` on the Deployment.

## How CI handles it

`validate-manifests.sh` verifies every `*.sops.yaml` is encrypted (contains
`ENC[`) and never decrypts in CI (the age key is deliberately NOT in CI). KSOPS apps
are validated statically. See [ci_policy.md](ci_policy.md).
