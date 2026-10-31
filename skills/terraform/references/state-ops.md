# State operations

Prefer config-driven blocks (reviewable in plan) over `terraform state` CLI (denied by hooks for `rm`).

| Task | Use | Example |
| --- | --- | --- |
| Rename resource / move into module | `moved` | `moved { from = aws_s3_bucket.logs  to = module.logs.aws_s3_bucket.this }` |
| Adopt existing resource | `import` (TF >= 1.5) | `import { to = aws_s3_bucket.this  id = "acme-logs" }` then `plan -generate-config-out=gen.tf` |
| Stop managing without deleting | `removed` (TF >= 1.7) | `removed { from = aws_s3_bucket.old  lifecycle { destroy = false } }` |
| count -> for_each | `moved` per index | `moved { from = aws_iam_user.u[0]  to = aws_iam_user.u["alice"] }` |
| Split state | `removed` in source + `import` in target, same PR window | Plan both; zero destroy expected |
| Backend migration | `terraform init -migrate-state` | Back up with `terraform state pull > backup.tfstate` first |
| Stuck lock | `terraform force-unlock <ID>` | Only after confirming no running apply |

Check after every state op: plan shows `0 to destroy` and no unexpected replace.
