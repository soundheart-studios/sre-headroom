# Module standards

| Item | Standard |
| --- | --- |
| Layout | `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md` |
| `versions.tf` | `required_version = ">= 1.9"`; every provider `~> X.Y` (G-0002) |
| Providers | Not configured inside modules; passed from root |
| Variables | `type` and `description` always; `validation` for enums and CIDRs; no defaults for env-specific values |
| Outputs | `description` always; mark secrets `sensitive = true` |
| Naming | `"${var.name}-${var.env}"`; resource local names are `this` for single-resource modules |
| Tags | `default_tags` at provider in root; module merges `var.tags` |
| Count vs for_each | `for_each` over maps/sets of strings; `count` only for 0/1 toggles |
| Lifecycle | `prevent_destroy = true` on data resources (RDS, S3 with data, KMS) |
| S3 | Public access block, SSE-KMS or SSE-S3, versioning, ownership controls `BucketOwnerEnforced` (G-0001) |
| IAM | `aws_iam_policy_document` data sources; explicit actions/resources (G-0007) |
| Root modules | One per env under `envs/<env>/`; remote state S3 + lock |
| Testing | `terraform test` with `*.tftest.hcl` for logic-heavy modules |
