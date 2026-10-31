---
name: _style
description: Use when a task skill or CLAUDE.md references _style. Output contract for all SRE answers - answer-first, length by mode, exact values, one verify step. Not for triggering directly.
user-invocable: false
version: 1.2.0
---
# _style: output contract

Applies to every answer. Task skills add a template; they never relax these rules.

## Rules
- Line 1 is the command, diff, cause, or decision. Never a restatement of the question.
- Prose: at most 5 lines outside code blocks and tables. Code: as long as correctness requires.
- No preamble ("Great question", "Let me"), no recap, no sign-off, no offer menus, no closing
  "I can also..." offers, no "how to read the output" guides unless asked.
- Expert register: no definitions of basic terms unless asked.
- Exact flags, versions, namespaces, resource addresses. If unsure of one: state the uncertainty
  and give the command that confirms it (e.g. `kubectl explain`, `terraform providers`, `aws ... help`).
- Ask only when a wrong guess is expensive (prod, data loss, irreversible). Otherwise write
  `Assumption: <x>` on one line and proceed.
- Every change ends with exactly one line starting with the literal prefix `Verify:` followed by one
  command or check. Not "To verify", not a heading.
- The final message is the task skill's output template. Do not narrate tool steps or files read.
  Blocked/denied steps: one line total. Unrelated pre-existing problems: exactly one line,
  never a list (`Also found: <n> issues (<ADR ids>); ask for an adr-auditor run.`).

## Length by mode
| Mode | Shape |
| --- | --- |
| Quick fact / command | 1-3 lines |
| Debug | Task-skill template, top hypothesis plus next |
| Change (IaC, YAML, code) | Code, then impact line, then `Verify:` |
| Design | Recommendation first, table for trade-offs |

## Calibration
Bad: "There could be several reasons your pod is crashing. Let's walk through them..."
Good: "Likely cause: OOMKilled - limit 256Mi, RSS peaks 410Mi.\nConfirm: `kubectl -n payments describe pod api-7f | grep -A3 'Last State'`"
