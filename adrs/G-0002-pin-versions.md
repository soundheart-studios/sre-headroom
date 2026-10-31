---
id: G-0002
title: Pin Terraform provider and module versions
status: accepted
scope: global
tags: [iac, terraform]
enforce: must
date: 2026-01-15
owners: [platform]
---
## Context
Unpinned providers broke plans on minor releases.

## Decision
All providers and modules are version-pinned.

## Rules
- `required_providers` uses `~> X.Y` for every provider.
- `required_version` is set in every root module.
- Registry modules pin an exact `version`; git modules pin `?ref=<tag>`, never a branch.
- `.terraform.lock.hcl` is committed.

## Consequences
Upgrades are explicit PRs.

## Exceptions
None.
