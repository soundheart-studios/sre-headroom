# ADR template

Fill every field. Tags from `~/.claude/adrs/TAGS.md` only. `status` starts `proposed`.

```markdown
---
id: "NNNN"            # repo: 4 digits; global: G-NNNN. From adr-next-id.sh
title: <decision as a phrase>
status: proposed
scope: repo           # repo | global
tags: [<1-5 tags>]
enforce: must         # must | should
supersedes: []        # ids replaced; may be global ids
date: YYYY-MM-DD
owners: [<team or handle>]
# applies_when: ["*.tf"]       # optional: globs; ADR is skipped in repos with no matching file
# policy: policies/<rule>.rego   # optional: OPA/conftest rule enforcing it
---
## Context
<= 5 lines: forces, constraints, what prompted the decision.

## Decision
<one line>

## Rules
- <testable rule>
- <testable rule>

## Consequences
<trade-offs accepted>

## Exceptions
<when deviation is allowed, or "None.">
```
