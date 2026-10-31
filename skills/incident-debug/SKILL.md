---
name: incident-debug
description: Use when something is broken, unhealthy, or degraded - keeps restarting, crashing, CrashLoopBackOff, OOMKilled, not ready, requests failing, 5xx, latency, timeouts, failed deploy, firing alert, odd logs - including "fix it" asks. Not for new manifests or IaC (k8s-manifests, terraform).
adr_tags: [observability, k8s, network]
requires: [_style, _adr, _safety]
version: 1.2.0
---
# incident-debug

## Step 0 (preloaded at skill load; do not re-read these files)
`_style` is already in context via CLAUDE.md; follow it exactly.
Risk rules:
!`cat ~/.claude/skills/_safety/SKILL.md`

ADR constraints for this repo (resolved for this skill's tags; apply per the rules in the output):
!`~/.claude/skills/_adr/scripts/adr-resolve.sh --soft --tags observability,k8s,network`
Touching files whose type adds tags (e.g. `*.py`, `*.ts`, CI)? Re-run once with `--files <paths>`.
How to apply them:
!`cat ~/.claude/skills/_adr/SKILL.md`

## Workflow
1. Classify. Active incident (alert firing, users impacted, "now", "prod down"): mitigation goes
   first (rollback, scale, failover), root cause second. Post-hoc: root cause first.
2. Gather. Kubernetes: `~/.claude/skills/incident-debug/scripts/k8s-triage.sh <ns> <workload>`
   (read-only). Any log file or log dump over ~100 lines: delegate to the `log-analyst` subagent
   with the path or workload, in the foreground (never `run_in_background`): wait for its report,
   then answer with the template using its top signatures as evidence. Never reply "waiting".
   If you have no cluster access, give the user the triage command instead of guessing output.
3. Match symptoms in references (table lookups, not narrative).
4. Rank hypotheses by probability x cost-to-check. Output the top one plus the next one only.
5. If blocked, ask for the single artifact that decides between the top two hypotheses.

## Output template
```text
Likely cause: <one line, specific: component, value, evidence>
Confirm: `<one read-only command with -n/--context/--region as needed>`
Fix: <command or diff; WARNING line first if disruptive>
If not: <next hypothesis> - `<command that confirms it>`
Verify: `<command that shows recovery>`
```
Active incident: prepend `Mitigate now: <command>` as line 1.

## References
- `references/k8s-failures.md` - read when the symptom is a pod/node/scheduling/probe state.
- `references/cloud-failures.md` - read when AWS APIs, IAM, quotas, LB, RDS, or managed services are involved.
- `references/network-failures.md` - read for DNS, timeouts, connection refused/reset, TLS, MTU.

## Calibration
Bad: "CrashLoopBackOff can have many causes, such as application errors, missing config, or resource limits. Let's check each."
Good:
```text
Likely cause: container exits on start - missing env DATABASE_URL after the ConfigMap rename in the last deploy.
Confirm: `kubectl -n payments logs deploy/api --previous --tail=50`
Fix: `kubectl -n payments rollout undo deploy/api`
If not: OOMKilled on start - `kubectl -n payments get pod -l app=api -o jsonpath='{..lastState.terminated.reason}'`
Verify: `kubectl -n payments rollout status deploy/api --timeout=120s`
```
