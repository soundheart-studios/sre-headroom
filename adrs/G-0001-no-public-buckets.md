---
id: G-0001
title: No public object storage buckets
status: accepted
scope: global
tags: [security, storage, aws]
enforce: must
date: 2026-01-15
owners: [platform-security]
applies_when: ["*.tf", "*.tfvars", "*bucket*.json"]
policy: policies/s3_public.rego
---
## Context
Public buckets caused two data exposures in 2025. Static content can be served without public buckets.

## Decision
No bucket may be publicly readable or writable.

## Rules
- Every `aws_s3_bucket` has an `aws_s3_bucket_public_access_block` with all four flags `true`.
- No bucket policy grants `Principal: "*"` without an `aws:SourceVpce` or `aws:PrincipalOrgID` condition.
- Public static content is served via CloudFront with Origin Access Control.

## Consequences
CloudFront required for public assets; slightly higher cost and setup.

## Exceptions
None without a repo ADR that lists G-0001 in `supersedes`.
