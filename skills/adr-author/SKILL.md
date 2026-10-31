---
name: adr-author
description: Use when drafting, updating, deprecating, or superseding an Architecture Decision Record (ADR) file. Not for checking whether an answer complies with ADRs (_adr) or auditing a repo (adr-auditor agent).
adr_tags: []
requires: [_style, _adr]
version: 1.1.0
---
# adr-author

## Step 0 (preloaded at skill load; do not re-read these files)
`_style` is already in context via CLAUDE.md; follow it exactly.
ADR constraints for this repo (resolved for this skill's tags; apply per the rules in the output):
!`~/.claude/skills/_adr/scripts/adr-resolve.sh --soft --tags iac,terraform,aws,k8s,helm,security,iam,storage,eda,messaging,schema,observability,code,ci,data`
Touching files whose type adds tags (e.g. `*.py`, `*.ts`, CI)? Re-run once with `--files <paths>`.
How to apply them:
!`cat ~/.claude/skills/_adr/SKILL.md`

## Workflow
1. Scope: repo decision -> `docs/adr/` (or repo CLAUDE.md path); org-wide -> `~/.claude/adrs/`.
2. Next id: `~/.claude/skills/_adr/scripts/adr-next-id.sh <adr-dir>`.
3. Fill `references/template.md` exactly. Tags only from `~/.claude/adrs/TAGS.md`.
   Rules must be testable bullets. Decision is one line.
4. Superseding: set `supersedes: [<old id>]` on the new ADR. If the old ADR is in the same
   repo, set its `superseded_by: "<new id>"` and leave its status (a human flips it to
   `superseded` when accepting the new one). A repo ADR may supersede a global one; never
   edit global ADRs from a repo task.
5. `status: proposed` always. Never set `accepted`; that is a human review step.
6. Regenerate the index: `~/.claude/skills/_adr/scripts/adr-index.sh <adr-dir>`.

## Output template
````text
<adr-dir>/<id>-<slug>.md
```markdown
<filled template>
```
Verify: `~/.claude/skills/_adr/scripts/adr-index.sh <adr-dir> --check`
````

## References
- `references/template.md` - read every time.

## Calibration
Bad: ADR with `status: accepted`, free-text tags, and a "Rules" section of prose.
Good: `docs/adr/0004-sqs-for-notifications.md`, `status: proposed`, tags `[messaging, aws]`,
`supersedes: []`, three testable rules, Exceptions filled.
