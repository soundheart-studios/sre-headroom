# Plan review

Run `plan-summary.sh plan.json` first; then check each row that applies.

| Signal in plan | Why it matters | Action |
| --- | --- | --- |
| Any `replace` (`-/+` or `+/-`) | Downtime or data loss for stateful resources | Find the forcing attribute (`# forces replacement`); use `create_before_destroy` or revert the attribute |
| Any `delete` | Irreversible for data resources | Confirm intent; for refactors use `moved {}` instead |
| Replace/delete of RDS, EBS, S3, DynamoDB, EFS, KMS key, MSK | Data loss | Block unless snapshot + explicit approval |
| `*_iam_*` changes | Privilege widening | Diff policy JSON; reject `*` actions (G-0007) |
| `*security_group*` with `0.0.0.0/0` or `::/0` | Public exposure | Reject unless public LB on 443 |
| `*_bucket_policy` / public access block change | Public data | Reject `Principal: "*"` without conditions (G-0001) |
| `*_kms_*` key policy or deletion window | Lockout / data loss | Two reviewers |
| Unknown values `(known after apply)` on name/id | Possible replace cascade | Check dependents |
| Provider version change in lock file | Behaviour drift | Separate PR (G-0002) |
| Drift (update with no code change) | Out-of-band change | Find who changed it; import or revert |

Verdict: `block` if destroy/replace of a data resource or an ADR `must` violation; `changes` if
flagged IAM/SG/policy issues; else `approve`.
