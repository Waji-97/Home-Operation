#!/usr/bin/env bash
#
# Policy checks (kube-linter) on FIRST-PARTY app manifests.
#
# Upstream Helm charts (kustomizations with a `helmCharts:` block) are skipped —
# we don't author them, and we keep them current via Renovate instead. Encrypted
# secrets and kustomize generator/config files are also skipped.
#
# Requirements: bash, find, grep, kube-linter.
# Local run:  ./scripts/policy-check.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rc=0
while IFS= read -r kfile; do
  dir="$(dirname "$kfile")"
  if grep -qs 'helmCharts:' "$kfile"; then
    echo "==> [skip: upstream helm] $dir"
    continue
  fi
  echo "==> [lint] $dir"
  files=()
  for rf in "$dir"/*.yaml; do
    case "$(basename "$rf")" in
      *.sops.yaml | secret-generator.yaml | kustomization.yaml) continue ;;
    esac
    [ -f "$rf" ] && files+=("$rf")
  done
  if [ "${#files[@]}" -gt 0 ]; then
    kube-linter lint --config .kube-linter.yaml "${files[@]}" || rc=1
  fi
done < <(find kubernetes/apps -name kustomization.yaml | sort)

echo
if [ "$rc" -ne 0 ]; then
  echo "POLICY CHECKS FAILED"
  exit 1
fi
echo "POLICY CHECKS PASSED"
