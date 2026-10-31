---
id: G-0003
title: Kubernetes workload baseline
status: accepted
scope: global
tags: [k8s, security]
enforce: must
date: 2026-02-01
owners: [platform]
---
## Context
OOM storms and noisy neighbours traced to workloads without requests and probes.

## Decision
Every workload meets the baseline before merge.

## Rules
- Every container sets cpu/memory `requests` and memory `limits`.
- Every long-running container has `readinessProbe` and `livenessProbe`.
- `securityContext`: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, drop `ALL` capabilities.
- Deployments with `replicas >= 2` have a PodDisruptionBudget.
- Images are pinned by tag plus digest or immutable tag; never `:latest`.

## Consequences
More YAML per workload.

## Exceptions
Jobs/CronJobs are exempt from probes and PDB.
