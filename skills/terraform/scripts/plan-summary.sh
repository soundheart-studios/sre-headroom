#!/usr/bin/env bash
# Usage: plan-summary.sh <plan.json>     (from: terraform show -json tfplan > plan.json)
# Read-only. Exit: 0 ok, 2 bad input, 4 destroy or replace present.
set -euo pipefail
plan="${1:?usage: plan-summary.sh <plan.json>}"
[[ -r "$plan" ]] || { echo "plan-summary: cannot read $plan" >&2; exit 2; }
jq -e '.resource_changes' "$plan" >/dev/null 2>&1 || { echo "plan-summary: no .resource_changes in $plan" >&2; exit 2; }

jq -r '
  def act: (.change.actions) as $a
    | if   ($a == ["delete","create"] or $a == ["create","delete"]) then "replace"
      elif $a == ["create"] then "create"
      elif $a == ["update"] then "update"
      elif $a == ["delete"] then "destroy"
      elif $a == ["read"]   then "read"
      else "no-op" end;
  def risky: .type | test("_iam_|security_group|_bucket_policy$|_kms_");
  [.resource_changes[] | {address, type, a: act}] as $rc
  | "== counts",
    ( ["create","update","replace","destroy"] | map(. as $k | "\($k): \([$rc[] | select(.a == $k)] | length)") | .[] ),
    "== replace/destroy",
    ( [$rc[] | select(.a == "replace" or .a == "destroy") | "\(.a)\t\(.address)"] | if length == 0 then ["none"] else . end | .[] ),
    "== flagged (iam / security group / bucket policy / kms)",
    ( [$rc[] | select(.a != "no-op" and .a != "read") | select(risky) | "\(.a)\t\(.address)"] | if length == 0 then ["none"] else . end | .[] )
' "$plan"

if jq -e '[.resource_changes[].change.actions | select(index("delete"))] | length > 0' "$plan" >/dev/null; then
  exit 4
fi
