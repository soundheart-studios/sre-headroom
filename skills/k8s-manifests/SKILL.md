---
name: k8s-manifests
description: Use when writing or changing Kubernetes manifests, Helm charts, values files, or Kustomize overlays - Deployments, Services, Ingress, HPA, PDB, RBAC. Not for diagnosing failing pods (incident-debug).
adr_tags: [k8s, helm, security]
requires: [_style, _adr, _safety]
version: 1.1.0
---
# k8s-manifests

## Step 0 (preloaded at skill load; do not re-read these files)
`_style` is already in context via CLAUDE.md; follow it exactly.
Risk rules:
!`cat ~/.claude/skills/_safety/SKILL.md`

ADR constraints for this repo (resolved for this skill's tags; apply per the rules in the output):
!`~/.claude/skills/_adr/scripts/adr-resolve.sh --soft --tags k8s,helm,security,ci`
Touching files whose type adds tags (e.g. `*.py`, `*.ts`, CI)? Re-run once with `--files <paths>`.
How to apply them:
!`cat ~/.claude/skills/_adr/SKILL.md`

## Workflow
1. Resolve ADRs (Step 0). Packaging format and baseline rules come from them.
2. Start from `references/baseline-workload.md`: requests/limits, probes, securityContext,
   PDB, topology spread. Match existing files in the repo (labels, namespace, chart layout).
3. Check `references/version-notes.md` for removed/changed APIs on the target cluster version.
4. Output full YAML for every changed object (no "..." elisions), then the diff command.
5. Never `kubectl apply`/`helm upgrade` yourself; output `kubectl diff` / `helm diff upgrade`.

## Output template
````text
<file path>
```yaml
<full manifest(s)>
```
Diff: `kubectl diff -k <overlay>` | `kubectl diff -f <file>` | `helm diff upgrade <rel> <chart> -f values-<env>.yaml -n <ns>`
Verify: `kubectl -n <ns> rollout status deploy/<name> --timeout=120s`
````

## References
- `references/baseline-workload.md` - read for every new workload; copy the baseline.
- `references/helm.md` - read when the repo packages with Helm.
- `references/version-notes.md` - read when the target version is known or an API looks old.

## Calibration
Bad: Deployment with `image: app:latest`, no resources, no probes, plus `kubectl apply -f`.
Good: Deployment with pinned image, requests/limits, probes, restricted securityContext, a PDB
(per ADR-G-0003), then `Diff: kubectl diff -k deploy/overlays/dev`.
