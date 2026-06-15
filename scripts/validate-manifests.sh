#!/usr/bin/env bash
#
# Validate the GitOps manifests. Runs in CI (.github/workflows/ci.yml) and locally.
#
# Checks:
#   1. Every *.sops.yaml is actually encrypted (never commit a plaintext secret).
#   2. Each kustomization renders and passes kubeconform schema validation.
#      - Apps using KSOPS are validated statically (their static resources only),
#        because the age private key is intentionally NOT available in CI.
#   3. Standalone Application manifests parse.
#
# Requirements: bash, find, grep, kustomize, kubeconform, helm (for --enable-helm).
# Local run:  ./scripts/validate-manifests.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rc=0
kubeconform_check() { kubeconform -strict -ignore-missing-schemas -summary "$@"; }

echo "==> 1. Ensure every *.sops.yaml is encrypted"
found_sops=0
while IFS= read -r f; do
  found_sops=1
  if grep -q 'ENC\[' "$f"; then
    echo "   ok (encrypted): $f"
  else
    echo "   ERROR: $f is PLAINTEXT — encrypt it with 'sops -e -i $f'"
    rc=1
  fi
done < <(find kubernetes -name '*.sops.yaml' ! -name '.sops.yaml')
[ "$found_sops" -eq 0 ] && echo "   (no *.sops.yaml files found)"

echo "==> 2. Validate kustomizations"
while IFS= read -r kfile; do
  dir="$(dirname "$kfile")"
  if grep -rqs 'kind: ksops' "$dir"; then
    echo "   [ksops -> static-only] $dir"
    for rf in "$dir"/*.yaml; do
      case "$(basename "$rf")" in
        *.sops.yaml | secret-generator.yaml | kustomization.yaml) continue ;;
      esac
      kubeconform_check "$rf" || rc=1
    done
  else
    echo "   [render] $dir"
    if ! kustomize build --enable-helm "$dir" | kubeconform_check; then
      rc=1
    fi
  fi
done < <(find kubernetes -name kustomization.yaml | sort)

echo "==> 3. Validate standalone Application manifests"
kubeconform_check kubernetes/bootstrap/in-cluster/root.yaml || rc=1

echo
if [ "$rc" -ne 0 ]; then
  echo "VALIDATION FAILED"
  exit 1
fi
echo "ALL CHECKS PASSED"
