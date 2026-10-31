---
name: code-change
description: Use when writing or modifying application or tooling code - Python, Go, TypeScript, shell, CI workflow files, tests, bug fixes in source. Not for Terraform (terraform), k8s YAML (k8s-manifests), or system design (eda-architecture).
adr_tags: [code, ci]
requires: [_style, _adr]
version: 1.1.0
---
# code-change

## Step 0 (preloaded at skill load; do not re-read these files)
`_style` is already in context via CLAUDE.md; follow it exactly.
ADR constraints for this repo (resolved for this skill's tags; apply per the rules in the output):
!`~/.claude/skills/_adr/scripts/adr-resolve.sh --soft --tags code,ci,observability,messaging,schema`
Touching files whose type adds tags (e.g. `*.py`, `*.ts`, CI)? Re-run once with `--files <paths>`.
How to apply them:
!`cat ~/.claude/skills/_adr/SKILL.md`

## Workflow
1. Resolve ADRs (Step 0): logging, event envelope, and messaging rules apply to code.
2. Read the files you change and one neighbour; match existing style, libraries, and layout.
3. Make the minimal diff that solves the request. No drive-by refactors or new dependencies
   unless asked.
4. Handle errors at boundaries (handlers, consumers, CLI entry). No bare `except`/`catch` that
   swallows; no silent fallbacks.
5. Add or update the test closest to the change when a test suite exists.
6. End with one line on how to run or test it, using the repo's commands from CLAUDE.md.

## Output template
````text
<file path>
```diff
<minimal diff>
```
Verify: `<exact test or run command>`
````

## Calibration
Bad: Rewriting the whole module, adding a new HTTP client library, and `except Exception: pass`.
Good: 6-line diff in `app/publisher.py` adding the CloudEvents `id` (per ADR-G-0005),
then `Verify: make test` (from repo CLAUDE.md).
