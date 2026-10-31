# Repo
kind-lab: local practice cluster for the agent-config demos. Owner: you.
Cluster: kind `converged`. Contexts: `kind-converged` (treat as dev), `lab-prod` (same cluster, treated as prod).
Namespace: `shop`. Everything here is disposable.

# Stack deltas
Plain manifests in `manifests/` (no Helm, no Kustomize) - see ADR-0001.

# Paths
ADRs: docs/adr/  Manifests: manifests/<workload>.yaml

# Commands
up: `make -C ../.. lab-up`   down: `make -C ../.. lab-down`
diff: `kubectl --context kind-converged diff -f manifests/<file>.yaml`
