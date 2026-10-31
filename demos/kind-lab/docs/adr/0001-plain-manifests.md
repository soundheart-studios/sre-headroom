---
id: "0001"
title: Plain manifests for the kind lab
status: accepted
scope: repo
tags: [k8s, helm]
enforce: must
supersedes: [G-0004]
date: 2026-10-31
owners: [sre]
---
## Context
The lab is a handful of throwaway workloads; packaging tooling adds nothing.

## Decision
Lab workloads are plain YAML files in `manifests/`, one file per workload.

## Rules
- One file per workload in `manifests/`, all objects in namespace `shop`.
- No Helm charts or Kustomize overlays.

## Consequences
No templating; duplication between files is accepted.

## Exceptions
None.
