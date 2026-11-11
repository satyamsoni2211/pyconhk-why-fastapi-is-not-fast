# Orders API demo: one command per demo step. Run `make` to list targets.
#
# Two setups, picked from .env:
#   Docker  (.env points at the compose `db` host):  make up && make seed
#   Local   (no .env, or one using localhost):       make seed, then `make gateway`
#                                                     and `make run` in two terminals

.DEFAULT_GOAL := help
SHELL := /bin/bash

UV        := uv run
BASE_URL  ?= http://localhost:8000
POOL_MODE ?= good
export BASE_URL

ifneq ($(shell grep -s '^DATABASE_URL=.*@db:' .env),)
  SETUP := docker
  # .env points at compose hostnames; tests run on the host, so use localhost.
  TEST_ENV := DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/orders \
              PAYMENT_GATEWAY_URL=http://localhost:8080
else
  SETUP := local
  TEST_ENV := PAYMENT_GATEWAY_URL=http://localhost:8080
endif

# Locust settings for ap5-load (override: make ap5-load USERS=50 DURATION=30s)
USERS    ?= 100
SPAWN    ?= 100
DURATION ?= 20s
# CSV prefix defaults to my-run-<pool mode the running app reports>
LIVE_POOL = $$(curl -s $(BASE_URL)/demo/ap5/info | python3 -c 'import sys,json;print(json.load(sys.stdin)["pool_mode"])')

# Wait until the app answers /health (up to 30s).
define wait_for_app
	@for i in $$(seq 1 30); do curl -sf $(BASE_URL)/health >/dev/null && exit 0; sleep 1; done; \
	  echo "App did not come up at $(BASE_URL)"; exit 1
endef

##@ Setup

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"} \
	  /^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)} \
	  /^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "Single endpoints: $(ENDPOINTS)" | fold -s -w 78 | sed '2,$$s/^/                  /'
	@echo
	@echo "Setup detected: $(SETUP)   (Docker if .env points at the db host, otherwise local SQLite)"

.PHONY: install
install: ## Install dependencies into the local venv (uv sync)
	uv sync

.PHONY: up
up: ## Docker: start postgres, gateway and app (POOL_MODE=good|bad)
	@test -f .env || { cp .env.example .env && echo "Created .env from .env.example"; }
	POOL_MODE=$(POOL_MODE) docker compose up -d --build
	$(wait_for_app)
	@curl -s $(BASE_URL)/demo/ap5/info; echo

.PHONY: down
down: ## Docker: stop the stack (data volume is kept)
	docker compose down

.PHONY: logs
logs: ## Docker: follow the app logs
	docker compose logs -f app

.PHONY: gateway
gateway: ## Local: run the mock payment gateway on :8080 (terminal 1)
	$(UV) uvicorn mock_gateway.main:app --port 8080

.PHONY: run
run: ## Local: run the app on :8000 (terminal 2; POOL_MODE=good|bad)
	@test "$(SETUP)" = local || { echo ".env points at Docker hosts (db, payment-gateway). Use 'make up', or remove .env for local mode."; exit 1; }
	POOL_MODE=$(POOL_MODE) $(UV) uvicorn app.main:app --port 8000

.PHONY: seed
seed: ## Seed 200 customers / 2000 orders (Postgres or SQLite; idempotent)
	$(UV) scripts/seed_data.py

.PHONY: health
health: ## Check the app and gateway are up
	@curl -sf $(BASE_URL)/health && echo "  app ok" || echo "app NOT reachable at $(BASE_URL)"
	@curl -sf -o /dev/null http://localhost:8080/get && echo "gateway ok" || echo "gateway NOT reachable on :8080"

.PHONY: baseline
baseline: ## Show the baseline (correct) endpoints
	curl -s "$(BASE_URL)/orders?limit=3"; echo

.PHONY: test
test: ## Run the pytest suite (starts the mock gateway if needed)
	$(TEST_ENV) $(UV) pytest tests/ -v

##@ Run every demo endpoint (scripts/demo_endpoints.py)

.PHONY: demos
demos: ap1 ap2 ap3 ap4 ap5 ## Run ap1 to ap5 one after another

.PHONY: ap1 ap2 ap3 ap4 ap5
ap1: ## AP1: bad vs good vs bridge, 3 concurrent + /health probe
	@$(UV) scripts/demo_endpoints.py ap1
ap2: ## AP2: bad vs good, 20 requests each
	@$(UV) scripts/demo_endpoints.py ap2
ap3: ## AP3: bad-crash vs bad-n1 vs good
	@$(UV) scripts/demo_endpoints.py ap3
ap4: ## AP4: bad vs good transform time at 500 orders
	@$(UV) scripts/demo_endpoints.py ap4
ap5: ## AP5: current pool mode + a burst of 200 requests
	@$(UV) scripts/demo_endpoints.py ap5

##@ Run a single endpoint (e.g. make ap1-bad)

ENDPOINTS := ap1-bad ap1-good ap1-bridge \
             ap2-bad ap2-good \
             ap3-bad-crash ap3-bad-n1 ap3-good \
             ap4-bad ap4-good \
             ap5-info ap5-query

.PHONY: $(ENDPOINTS) endpoints
endpoints: ## List every single-endpoint target
	@echo $(ENDPOINTS) | tr ' ' '\n'

# ap3-bad-crash -> demo_endpoints.py ap3 bad-crash
$(ENDPOINTS):
	@$(UV) scripts/demo_endpoints.py $(firstword $(subst -, ,$@)) $(patsubst $(firstword $(subst -, ,$@))-%,%,$@)

##@ Profiling and benchmark scripts

.PHONY: ap1-debug ap1-flamegraph ap2-bench ap3-echo ap4-profile ap5-bad ap5-good ap5-load ap5-ui
ap1-debug: ## AP1: asyncio debug mode flags the blocking call
	$(UV) scripts/ap1_asyncio_debug.py

ap1-flamegraph: ## AP1: py-spy flame graph (Docker only; MODE=bad|good|bridge)
	@test "$(SETUP)" = docker || { echo "ap1-flamegraph needs the Docker setup (make up)."; exit 1; }
	./scripts/ap1_pyspy_flamegraph.sh $(or $(MODE),bad) flamegraph-$(or $(MODE),bad).svg

ap2-bench: ## AP2: 50 sequential requests each, mean/p50/p95
	$(UV) scripts/ap2_di_benchmark.py

ap3-echo: ## AP3: print every SQL statement and count them
	$(UV) scripts/ap3_sqlalchemy_echo.py

ap4-profile: ## AP4: cProfile call counts (rewrites benchmarks/ap4-pydantic/*.txt)
	$(UV) scripts/ap4_pydantic_cprofile.py

ap5-bad: ## AP5: restart the app with the small pool, then burst it
	@$(MAKE) --no-print-directory _ap5-restart POOL_MODE=bad
	@$(UV) scripts/demo_endpoints.py ap5

ap5-good: ## AP5: restart the app with the large pool, then burst it
	@$(MAKE) --no-print-directory _ap5-restart POOL_MODE=good
	@$(UV) scripts/demo_endpoints.py ap5

ap5-load: ## AP5: headless locust run against the current pool (CSV=prefix)
	$(UV) locust --headless -u $(USERS) -r $(SPAWN) -t $(DURATION) \
	  --host $(BASE_URL) --csv $(or $(CSV),my-run-$(LIVE_POOL)) -f scripts/ap5_locustfile.py

ap5-ui: ## AP5: locust web UI on http://localhost:8089
	$(UV) locust -f scripts/ap5_locustfile.py --host $(BASE_URL)

.PHONY: _ap5-restart
_ap5-restart:
ifeq ($(SETUP),docker)
	POOL_MODE=$(POOL_MODE) docker compose up -d app
	$(wait_for_app)
else
	@echo "Local setup: stop 'make run' (Ctrl-C) and start 'make run POOL_MODE=$(POOL_MODE)', then press Enter."; read _
endif
