---
id: "0003"
title: Prod changes only through CI
status: accepted
scope: repo
tags: [ci, terraform, k8s]
enforce: must
date: 2026-05-01
owners: [payments-sre]
---
## Context
A manual `kubectl apply` to prod in March 2026 skipped review and caused a 40-minute outage.

## Decision
Prod Terraform and Kubernetes changes are applied only by the CI deploy workflow.

## Rules
- No local `terraform apply` or `kubectl apply` against `envs/prod` or context `eks-prod`.
- Prod changes are PRs; CI posts the plan/diff; merge triggers apply.

## Consequences
Hotfixes take a PR (~10 minutes).

## Exceptions
Break-glass rollback (`kubectl rollout undo`) during a declared SEV1, logged in the incident doc.
