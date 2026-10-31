# Repo
payments-platform: order + payment services and their AWS infra. Owners: @payments-sre.
Envs: dev (account 111111111111, kube context `eks-dev`), prod (account 222222222222, kube context `eks-prod`).
Terraform roots: `envs/dev`, `envs/prod`. Prod changes ship only through CI (ADR-0003).

# Stack deltas
Kustomize, not Helm (ADR-0002). Kafka on MSK for events (ADR-0001). Python 3.12 services.
Namespace: `payments`. Kafka topics: `orders.v1`, `payments.v1`.

# Paths
ADRs: docs/adr/  Modules: modules/  Envs: envs/<env>/  Manifests: deploy/base, deploy/overlays/<env>
App: app/  Tests: tests/  Fixtures for demos: fixtures/

# Commands
lint: `make lint`   test: `make test` (pytest)   plan: `terraform -chdir=envs/<env> plan -out=tfplan`
deploy: CI only (`.github/workflows/deploy.yml`); local diff: `kubectl diff -k deploy/overlays/<env>`
