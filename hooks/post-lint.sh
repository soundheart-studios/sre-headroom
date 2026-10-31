#!/usr/bin/env bash
# PostToolUse(Write|Edit|MultiEdit): terraform fmt/tflint on *.tf, kubeconform on k8s YAML.
# Missing linters are skipped silently (make deps installs them). Findings -> exit 2 (reported to agent).
set -uo pipefail
file="$(jq -r '.tool_input.file_path // empty')"
[[ -f "$file" ]] || exit 0
out=""
case "$file" in
  *.tf)
    command -v terraform >/dev/null && { r="$(terraform fmt -check -diff "$file" 2>&1)" || out+="terraform fmt:\n$r\n"; }
    command -v tflint >/dev/null && { r="$(tflint --chdir "$(dirname "$file")" 2>&1)" || out+="tflint:\n$r\n"; }
    ;;
  *.yaml|*.yml)
    if grep -qE '^(apiVersion|kind):' "$file" && ! grep -q '{{' "$file"; then
      command -v kubeconform >/dev/null && { r="$(kubeconform -strict -summary -ignore-missing-schemas "$file" 2>&1)" || out+="kubeconform:\n$r\n"; }
    fi
    ;;
esac
if [[ -n "$out" ]]; then printf "agent-config post-lint findings for %s:\n%b" "$file" "$out" >&2; exit 2; fi
exit 0
