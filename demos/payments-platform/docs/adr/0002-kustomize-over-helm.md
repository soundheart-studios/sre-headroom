---
id: "0002"
title: Kustomize over Helm for payments workloads
status: accepted
scope: repo
tags: [k8s, helm]
enforce: must
supersedes: [G-0004]
date: 2026-04-10
owners: [payments-sre]
---
## Context
All payments workloads are first-party with 2 envs; Helm templating added review noise without reuse.

## Decision
Package payments workloads with Kustomize base + per-env overlays; no Helm charts in this repo.

## Rules
- Manifests live in `deploy/base/` with overlays in `deploy/overlays/<env>/`.
- No `Chart.yaml` or Helm templates in this repo.
- Review changes with `kubectl diff -k deploy/overlays/<env>`.

## Consequences
No Helm rollback; rollback is `kubectl rollout undo` or reverting the overlay commit.

## Exceptions
Third-party charts (e.g. cert-manager) are installed by the platform repo, not here.
