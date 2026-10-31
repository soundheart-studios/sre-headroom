---
name: _safety
description: Use when a task skill references _safety or an answer contains a risky command. Risk flags, reversible-path-first, prod confirmation. Not for triggering directly.
user-invocable: false
adr_tags: [security, iam]
version: 1.0.0
---
# _safety: risk flags

Hooks and permission denies are the enforcement layer. These rules shape what you propose.

## Flag these with a `WARNING:` line immediately before the command or block
- destroy or replace of any resource; Terraform state operations
- data loss: drop/truncate, bucket/volume/snapshot deletion, retention reduction
- disruption: drain, cordon, rollout restart, failover, scale to zero, node group replace
- IAM or network widening: new principals, wildcard actions, 0.0.0.0/0, new public endpoints
- public exposure of storage or services
- secrets landing in state, logs, env vars, or plan output
- irreversible deletes of any kind

Format: `WARNING: <what breaks> - <blast radius>. Reversible path: <cmd>.`

## Prefer the reversible path first
| Instead of | Offer first |
| --- | --- |
| `terraform apply` | `terraform plan -out=tfplan` then review with plan-summary |
| `kubectl apply` | `kubectl diff -f` or `kubectl apply --dry-run=server -f` |
| `helm upgrade` | `helm diff upgrade` then `helm upgrade --atomic` |
| big-bang rollout | canary, `maxUnavailable: 0`, feature flag |
| `terraform state rm/mv` | `removed` / `moved` / `import` blocks |

## Prod
- A prod target (context, workspace, profile, or path containing `prod`) requires the user to say
  "prod" in the request. If they did not, stop and ask: `Confirm target env: prod?`
- Mutating commands by environment:
  - dev/local (kind, minikube, `*-dev` contexts, `envs/dev`): when the user asked for a fix, run the
    apply yourself (`kubectl apply`, `helm upgrade`) after a diff; the permission prompt is the gate.
  - prod, or env unknown: output the command for the user; never run it.
  - Always denied (destroy, delete, drain, state rm): output for the user; never attempt.
- If a hook blocks a command, report the block in one line; do not retry a variant.
