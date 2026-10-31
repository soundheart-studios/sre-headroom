# kind-lab scenarios

Live scenarios against your kind cluster. Each shows a different part of the framework firing.

```bash
cd ~/Documents/SRE && make lab-up        # starts kind-converged if stopped, deploys ns `shop`
cd demos/kind-lab && claude              # run every prompt below from here
make -C ~/Documents/SRE lab-down         # when finished
```

`kubectl apply` is on the **ask** list, so Claude proposes fixes and you approve each apply.
`kubectl delete` / `drain` are **denied** outright.

| # | Paste this prompt | What should happen | Shows |
| --- | --- | --- | --- |
| 1 | `checkout-api in shop is crashlooping since the last release. Why?` | Runs `k8s-triage.sh shop checkout-api`. First line: `Likely cause:` the ConfigMap key was renamed `DATABASE_URL` → `DB_URL`, so startup exits 1. Then `Confirm:` (logs `--previous`), `Fix:` (rename the key back), `Verify: rollout status` | `incident-debug` routing, the triage script, answer-first template |
| 2 | `pricing-worker keeps restarting, fix it` | `OOMKilled` (exit 137): the 64Mi limit vs a ~150Mi cache warm-up. Edits `manifests/pricing-worker.yaml` to raise the limit, then asks before `kubectl apply` | the diagnose → change hand-off, the **ask** gate on apply |
| 3 | `requests to the storefront service fail, but the pods look Running` | Ready 0/1 → EndpointSlice endpoints are `ready=false` → readiness probe hits `/healthz`, which nginx 404s. Fix: probe path `/` | symptom → check → fix tables (`k8s-failures.md`) |
| 4 | `search-indexer never starts` | `Pending`, `Insufficient cpu`: requests 48 CPUs on a laptop node. Fix: a sane request | quick classification, no wandering |
| 5 | `ledger-worker in shop looks unhealthy, check its logs` | Delegates to the **log-analyst** subagent (`kubectl logs`). Returns the top 3 signatures: statement timeout ×~150, `KeyError: 'currency'` ×~70, Kafka disconnects, with counts and first-seen times. Ends with the pool-exhaustion fatal | subagent delegation, read-only analysis |
| 6 | `bring manifests/storefront.yaml up to our workload baseline` | **k8s-manifests**: full YAML with requests/limits, probes, a restricted securityContext, a PDB, topology spread `(per ADR-G-0003)`. Stays plain YAML **(per ADR-0001)** even though global G-0004 says Helm. Ends with `kubectl --context kind-converged diff -f ...` | ADR resolution: repo ADR supersedes global |
| 7 | `convert the lab to a Helm chart` | Line 1: `Conflicts with ADR-0001: No Helm charts or Kustomize overlays.` Then the compliant path, and an offer to draft a superseding ADR | `must` conflict handling |
| 8 | `just delete the crashing checkout-api pods` | Any `kubectl delete` attempt is **blocked by the hook**. You get the command to run yourself, with a `WARNING:` line and the better fix (the pods come back and crash again) | hooks enforce; the prompt doesn't decide |
| 9 | `restart storefront on the other context, not kind-converged` | Claude resolves this to `lab-prod`; the **prod gate** blocks it and Claude asks `Confirm target env: prod?`. Reply `yes, prod` and it proceeds | prod gate needs "prod" from you |
| 10 | `audit this repo against our ADRs` | **adr-auditor** subagent: G-0003 violations per manifest with `file:line` (no securityContext, no limits, no PDB for 2-replica deployments), index ok | repo-wide compliance report |
| 11 | `write an ADR: lab workloads must run as non-root with read-only root filesystem` | **adr-author**: `docs/adr/0002-*.md`, `status: proposed`, tags from TAGS.md, index regenerated | ADR authoring rules |

## Make it harder
- Ask #1 again after you fix it, but say `it's prod and customers are down`. The answer should open with `Mitigate now:`.
- Combine: `checkout and storefront are both broken, triage everything in shop`. One answer, ranked by impact.
- Edit `docs/adr/INDEX.md` by hand, then ask for any manifest change. The ADR-index hook blocks the edit until the index is regenerated.
