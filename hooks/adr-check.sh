#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit): block edits while repo or global ADR INDEX.md is stale/invalid.
# Edits to ADR files themselves are allowed (the agent regenerates the index after).
set -uo pipefail
here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
idx="$here/../skills/_adr/scripts/adr-index.sh"
input="$(cat)"
file="$(jq -r '.tool_input.file_path // empty' <<<"$input")"
cwd="$(jq -r '.cwd // empty' <<<"$input")"; cwd="${cwd:-$PWD}"
case "$file" in */docs/adr/*|*/adrs/*) exit 0;; esac

dirs=("$here/../adrs")
d="$cwd"
while [[ "$d" != "/" ]]; do
  if [[ -d "$d/docs/adr" ]]; then dirs+=("$d/docs/adr"); break; fi
  [[ -d "$d/.git" ]] && break
  d="$(dirname "$d")"
done
for adr_dir in "${dirs[@]}"; do
  out="$("$idx" "$adr_dir" --check 2>&1)"; rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "BLOCKED by agent-config adr-check: $out" >&2
    echo "Regenerate: ~/.claude/skills/_adr/scripts/adr-index.sh $adr_dir   (fix invalid ADRs first if exit 2)" >&2
    exit 2
  fi
done
exit 0
