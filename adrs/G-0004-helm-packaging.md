---
id: G-0004
title: Helm for Kubernetes packaging
status: accepted
scope: global
tags: [k8s, helm]
enforce: should
date: 2026-02-01
owners: [platform]
---
## Context
Mixed Helm/Kustomize/raw YAML made rollbacks inconsistent.

## Decision
Package workloads as Helm charts.

## Rules
- New workloads ship as a Helm chart with `values-<env>.yaml` per environment.
- Diffs are reviewed with `helm diff upgrade` before rollout.

## Consequences
Template complexity for small apps.

## Exceptions
Repos may choose Kustomize via a superseding repo ADR.
