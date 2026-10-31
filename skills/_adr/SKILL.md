---
name: _adr
description: Use when a task skill references _adr or before any design, IaC, k8s, messaging, or code change. Resolves accepted repo and global ADRs by tag and applies them as constraints. Not for authoring ADRs (adr-author).
user-invocable: false
version: 1.1.0
---
# _adr: resolve ADRs

## Run
Task skills preload this output at Step 0. Run it yourself only when touched files add tags,
or when no task skill is active. From the repo root (cwd), as a single command:
```bash
~/.claude/skills/_adr/scripts/adr-resolve.sh --tags <t1,t2> [--files <paths>]  # one command, no cd/&& chaining
```
The script resolves in order: repo `docs/adr/` first, then global `~/.claude/adrs/`;
`status=accepted` only; tag intersection; globals listed in a repo ADR's `supersedes` dropped.
Its output is the full constraint set. Do not open ADR files unless you need `Context`.

## Apply
- `must`: hard constraint. Write the answer so it complies.
- `should`: the default. Deviate only with one stated reason, and cite it.
- Cite every ADR-driven choice inline: `(per ADR-<id>)`.
- Silent otherwise: never list ADRs that do not change the answer.

## Conflicts
| Situation | Do |
| --- | --- |
| Request violates a `must` | First line: `Conflicts with ADR-<id>: <rule>.` Give the compliant answer; offer an `adr-author` superseding draft |
| Request violates a `should` | Proceed only with a stated reason; cite the ADR |
| Repo and global ADR contradict, no `supersedes` link | Follow repo; one line: `ADR-<repo-id> contradicts ADR-<global-id> without a supersedes link - add one.` |
| Significant decision, no ADR covers it | Answer, then one line offering an `adr-author` draft |
| ADR names a removed tool/version or script marks it stale | Follow it; flag `stale: ADR-<id>` |

## Index hygiene
If the script exits 2, report the invalid ADR. If an edit is blocked for a stale index, run
`~/.claude/skills/_adr/scripts/adr-index.sh <dir>` and retry.
