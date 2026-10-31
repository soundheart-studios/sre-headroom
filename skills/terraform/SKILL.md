---
name: terraform
description: Use when writing, changing, reviewing, importing, or refactoring Terraform/OpenTofu - .tf files, modules, providers, state moves, plan review. Not for debugging live outages (incident-debug) or k8s YAML (k8s-manifests).
adr_tags: [iac, terraform, aws]
requires: [_style, _adr, _safety]
version: 1.1.0
---
# terraform

## Step 0 (preloaded at skill load; do not re-read these files)
`_style` is already in context via CLAUDE.md; follow it exactly.
Risk rules:
!`cat ~/.claude/skills/_safety/SKILL.md`

ADR constraints for this repo (resolved for this skill's tags; apply per the rules in the output):
!`~/.claude/skills/_adr/scripts/adr-resolve.sh --soft --tags iac,terraform,aws,security,iam,storage,network,ci`
Touching files whose type adds tags (e.g. `*.py`, `*.ts`, CI)? Re-run once with `--files <paths>`.
How to apply them:
!`cat ~/.claude/skills/_adr/SKILL.md`

## Workflow
1. Resolve ADRs (Step 0). Pinning, public access, and IAM rules from ADRs are hard constraints.
2. Read the existing module/env files you change. Match naming and layout from repo CLAUDE.md.
   New module: read `references/module-standards.md`. Import, move, rename, split state:
   read `references/state-ops.md`.
3. Write only the changed blocks, with file paths. Pin providers/modules.
4. Prefer `moved {}`, `import {}`, and `removed {}` blocks over `terraform state` CLI.
5. Any request to review/check/approve a plan (plan.json, tfplan, or plan output): delegate to the
   `plan-reviewer` subagent with the plan path. Do not review inline. Relay its verdict block as-is,
   then add at most one line of your own. (It runs `plan-summary.sh`; exit 4 = destroy/replace.)
6. Never run `apply`/`destroy` (blocked by hooks). Output `plan` for the user.

## Output template
````text
<file path>
```hcl
<changed blocks only>
```
Plan impact: <N create / N update / N replace / N destroy, name any replace/destroy>
WARNING: ... (only if _safety applies)
Verify: `terraform -chdir=<dir> plan -out=tfplan`
````

## References
- `references/module-standards.md` - read when creating or restructuring a module.
- `references/state-ops.md` - read for import, moved, removed, state split, or backend changes.
- `references/plan-review.md` - read when interpreting plan-summary output outside a plan-reviewer run.

## Calibration
Bad: "Here's a complete Terraform configuration for your S3 bucket:" followed by an unpinned provider and no public access block.
Good: `modules/bucket/main.tf` diff adding `aws_s3_bucket_public_access_block` (per ADR-G-0001), then
`Plan impact: 1 create, 0 replace`, then `Verify: terraform -chdir=envs/dev plan -out=tfplan`.
