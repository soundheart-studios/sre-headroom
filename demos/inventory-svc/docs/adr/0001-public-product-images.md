---
id: "0001"
title: Public-read bucket for product images
status: accepted
scope: repo
tags: [storage, aws]
enforce: must
date: 2026-06-12
owners: [catalog-team]
---
## Context
Partner storefronts hotlink product images directly from S3 URLs baked into feeds; changing URLs needs a 6-month partner migration.

## Decision
The `acme-product-images` bucket stays public-read until partner feeds migrate.

## Rules
- Only the `acme-product-images-<env>` bucket may allow public `s3:GetObject`.
- No public write, no public list.
- Every other bucket follows the platform default (private).

## Consequences
Images are publicly enumerable by key guessing.

## Exceptions
None.
