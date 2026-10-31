---
id: G-0007
title: IAM least privilege, no wildcard actions
status: accepted
scope: global
tags: [iam, security, aws]
enforce: must
date: 2026-01-15
owners: [platform-security]
applies_when: ["*.tf", "*.tfvars", "*policy*.json"]
policy: policies/iam_wildcard.rego
---
## Context
Wildcard policies widened blast radius in a 2025 incident.

## Decision
IAM policies grant explicit actions on explicit resources.

## Rules
- No `"Action": "*"` or `"<service>:*"` in any policy.
- No `"Resource": "*"` except for actions that do not support resource-level permissions.
- Workloads on EKS use IRSA or Pod Identity; never node-role permissions.

## Consequences
More policy statements to maintain.

## Exceptions
Break-glass roles defined in the security account only.
