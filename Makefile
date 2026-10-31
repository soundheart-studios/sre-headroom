# sre-headroom: layered Claude Code skills + ADR framework for SRE work
CLAUDE_HOME ?= $(HOME)/.claude
PY          := python3
AGENTCFG    := $(PY) install/agentcfg.py --claude-home $(CLAUDE_HOME)
EVAL_ARGS   ?=

.DEFAULT_GOAL := help
.PHONY: lab-up lab-down lab-status lab-reset help install uninstall reinstall status dry-run deps check validate unit index eval eval-smoke clean

help: ## Show targets
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

install: check ## Validate, then link skills/agents/adrs into ~/.claude and merge settings + CLAUDE.md import
	@$(AGENTCFG) install

uninstall: ## Remove exactly what install added (manifest-driven); your other config is untouched
	@$(AGENTCFG) uninstall

reinstall: uninstall install ## Uninstall then install

status: ## Show install state
	@$(AGENTCFG) status

dry-run: ## Print what install would change, change nothing
	@$(AGENTCFG) install --dry-run

deps: ## Install required (yq, jq) and optional lint tools used by hooks (terraform, tflint, kubeconform)
	brew install yq jq
	-brew install hashicorp/tap/terraform tflint kubeconform

check: validate unit ## Static validation + deterministic tests (no model calls)

validate: ## Static checks (frontmatter, budgets, overlap, ADR indexes, coverage)
	@ci/validate.sh

unit: ## Script, hook, validator, installer tests
	@$(PY) tests/unit/test_framework.py

index: ## Regenerate all ADR INDEX.md files
	@skills/_adr/scripts/adr-index.sh adrs
	@for d in demos/*/docs/adr; do skills/_adr/scripts/adr-index.sh $$d; done

eval: ## Behavior evals with real claude sessions (needs install). EVAL_ARGS="--only 'terraform-*' --model sonnet --jobs 4 --repeat 3"
	@$(PY) tests/run_evals.py $(EVAL_ARGS)

eval-smoke: ## One case per skill + safety
	@$(PY) tests/run_evals.py --only '*-crashloop' $(EVAL_ARGS); \
	 $(PY) tests/run_evals.py --only 'terraform-adr-conflict-public' $(EVAL_ARGS)

clean: ## Remove eval results
	rm -rf tests/results

# ---- kind lab (demos/kind-lab): broken workloads for live scenarios
KIND_CLUSTER ?= converged
KCTX         := kind-$(KIND_CLUSTER)

lab-up: ## Start kind cluster if stopped, add lab-prod context alias, deploy broken workloads to ns shop
	@docker start $(KIND_CLUSTER)-control-plane >/dev/null 2>&1 || kind create cluster --name $(KIND_CLUSTER)
	@for i in $$(seq 1 60); do kubectl --context $(KCTX) get --raw /readyz >/dev/null 2>&1 && break; sleep 2; done
	@kubectl config set-context lab-prod --cluster=$(KCTX) --user=$(KCTX) --namespace=shop >/dev/null
	@kubectl --context $(KCTX) apply -f demos/kind-lab/manifests/00-namespace.yaml -f demos/kind-lab/manifests/
	@echo "lab up: kubectl --context $(KCTX) -n shop get pods   (give it ~60s to break properly)"

lab-down: ## Remove ns shop and the lab-prod context (cluster left running; docker stop it yourself)
	-@kubectl --context $(KCTX) delete namespace shop --wait=false
	-@kubectl config delete-context lab-prod >/dev/null 2>&1
	@echo "lab down"

lab-reset: ## Restore broken manifests from demos/kind-lab/pristine and re-apply them
	@cp demos/kind-lab/pristine/*.yaml demos/kind-lab/manifests/
	@kubectl --context $(KCTX) apply -f demos/kind-lab/manifests/00-namespace.yaml -f demos/kind-lab/manifests/
	@kubectl --context $(KCTX) -n shop rollout restart deploy >/dev/null
	@echo "lab reset to broken state"

lab-status: ## Pod state in the lab
	@kubectl --context $(KCTX) -n shop get pods,svc,endpointslices -o wide
