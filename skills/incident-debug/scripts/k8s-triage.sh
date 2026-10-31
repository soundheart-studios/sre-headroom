#!/usr/bin/env bash
# Usage: k8s-triage.sh <namespace> <workload>   workload: name, or kind/name (deploy/api, sts/db)
# Read-only: get, describe, logs, top, events only. Exit: 0 ok, 2 usage/no kubectl, 3 workload not found.
set -euo pipefail
ns="${1:-}"; wl="${2:-}"
[[ -n "$ns" && -n "$wl" ]] || { echo "usage: k8s-triage.sh <namespace> <workload>" >&2; exit 2; }
command -v kubectl >/dev/null || { echo "k8s-triage: kubectl not found" >&2; exit 2; }
[[ "$wl" == */* ]] || wl="deploy/$wl"
k() { kubectl -n "$ns" "$@"; }

echo "== context: $(kubectl config current-context 2>/dev/null || echo none)  namespace: $ns  workload: $wl"
k get "$wl" -o wide >/dev/null 2>&1 || { echo "k8s-triage: $wl not found in $ns" >&2; exit 3; }

echo "== status"
k get "$wl" -o wide
sel="$(k get "$wl" -o jsonpath='{.spec.selector.matchLabels}' | jq -r 'to_entries | map("\(.key)=\(.value)") | join(",")')"
k get pods -l "$sel" -o wide
pod="$(k get pods -l "$sel" --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')"

echo "== last 20 events"
k get events --sort-by=.lastTimestamp 2>/dev/null | tail -20

if [[ -n "$pod" ]]; then
  echo "== describe pod/$pod (trimmed)"
  k describe "pod/$pod" | sed -n '/^Containers:/,/^Volumes:/p' | grep -E 'State|Reason|Exit Code|Restart Count|Last State|Limits|Requests|memory|cpu|Liveness|Readiness|Image:' || true
  echo "== logs pod/$pod (current, 200)"
  k logs "pod/$pod" --all-containers --tail=200 2>&1 || true
  echo "== logs pod/$pod (previous, 200)"
  k logs "pod/$pod" --all-containers --previous --tail=200 2>&1 || echo "(no previous container)"
fi

echo "== resource usage"
k top pods -l "$sel" 2>&1 || echo "(metrics unavailable)"
