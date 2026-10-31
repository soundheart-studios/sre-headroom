# Repo
inventory-svc: stock levels API + product image assets. Owners: @catalog-team.
Envs: dev (context `eks-dev`, namespace `inventory`), prod (context `eks-prod`). Single Terraform root in `infra/` with workspaces `dev`/`prod`.

# Stack deltas
TypeScript on Node 22 (ADR-0003). Helm chart in `chart/` (follows global packaging ADR).

# Paths
ADRs: docs/adr/  Terraform: infra/  Chart: chart/ (values-<env>.yaml)  Source: src/

# Commands
lint: `npm run lint`   test: `npm test`   plan: `terraform -chdir=infra workspace select <env> && terraform -chdir=infra plan`
diff: `helm diff upgrade inventory chart -f chart/values-<env>.yaml -n inventory`
