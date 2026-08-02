# ============================================
# 💫 Makefile
# --------------------------------------------

# === 🧱 BASE CONFIGURATION ===================

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

PACKAGE := pytestquick
DIST_NAME := pytestquick
CLI_NAME := pytestquick

DIST_DIR := dist
BUILD_DIR := build
WHEEL_TEST_DIR := /tmp/$(PACKAGE)-wheel-test

# ============================================
# 📦 ENVIRONMENT / DEPENDENCIES
# --------------------------------------------

.PHONY: sync lock upgrade

sync: ## Install and synchronize project dependencies
	uv sync --dev

lock: ## Refresh the lockfile without upgrading packages
	uv lock

upgrade: ## Upgrade locked dependencies
	uv lock --upgrade
	uv sync --dev

# ============================================
# 🧹 FORMAT / LINT / TYPE CHECK
# --------------------------------------------

.PHONY: format format-check lint typecheck

format: ## Format Python files and apply Ruff fixes
	uv run ruff format .
	uv run ruff check . --fix

format-check: ## Verify formatting without changing files
	uv run ruff format . --check

lint: ## Run Ruff lint checks
	uv run ruff check .

typecheck: ## Run mypy
	uv run mypy src tests

# ============================================
# 🧪 TESTING & COVERAGE
# --------------------------------------------

.PHONY: test test-fast coverage

test: ## Run the complete test suite
	uv run pytest

test-fast: ## Run tests in parallel
	uv run pytest -n auto

coverage: ## Run tests with branch coverage
	uv run pytest \
		--cov=$(PACKAGE) \
		--cov-branch \
		--cov-report=term-missing \
		--cov-report=html

# ============================================
# ✅ PROJECT VALIDATION
# --------------------------------------------

.PHONY: check ci

check: format-check lint typecheck test ## Run all local validation checks

ci: ## Run the complete CI validation pipeline
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) coverage
	$(MAKE) build
	$(MAKE) check-dist

# ============================================
# 🏗️ BUILD / PACKAGE VALIDATION
# --------------------------------------------

.PHONY: build check-dist wheel-contents install-wheel release-check

build: clean-build ## Build source and wheel distributions
	uv run python -m build

check-dist: ## Validate built distributions with Twine
	@test -d "$(DIST_DIR)" || { \
		echo "Missing $(DIST_DIR)/. Run 'make build' first."; \
		exit 1; \
	}
	@files="$$(find "$(DIST_DIR)" -maxdepth 1 -type f -print)"; \
	if [ -z "$$files" ]; then \
		echo "No distributions found. Run 'make build' first."; \
		exit 1; \
	fi
	uv run twine check $(DIST_DIR)/*

wheel-contents: ## List files included in the built wheel
	@wheel="$$(find "$(DIST_DIR)" -maxdepth 1 -name '*.whl' -print -quit)"; \
	if [ -z "$$wheel" ]; then \
		echo "No wheel found. Run 'make build' first."; \
		exit 1; \
	fi; \
	unzip -l "$$wheel"

install-wheel: ## Install and validate the wheel in a clean environment
	@wheel="$$(find "$(DIST_DIR)" -maxdepth 1 -name '*.whl' -print -quit)"; \
	if [ -z "$$wheel" ]; then \
		echo "No wheel found. Run 'make build' first."; \
		exit 1; \
	fi; \
	rm -rf "$(WHEEL_TEST_DIR)"; \
	trap 'rm -rf "$(WHEEL_TEST_DIR)"' EXIT; \
	uv venv "$(WHEEL_TEST_DIR)"; \
	uv pip install \
		--python "$(WHEEL_TEST_DIR)/bin/python" \
		"$$wheel"; \
	"$(WHEEL_TEST_DIR)/bin/python" -c \
		'import pytestquick; from importlib.metadata import version; print("Installed:", version("$(DIST_NAME)"), pytestquick.__file__)'; \
	test -x "$(WHEEL_TEST_DIR)/bin/$(CLI_NAME)"; \
	"$(WHEEL_TEST_DIR)/bin/$(CLI_NAME)" --help

release-check: ## Run full release validation
	$(MAKE) clean
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) coverage
	$(MAKE) build
	$(MAKE) check-dist
	@wheel="$$(find "$(DIST_DIR)" -maxdepth 1 -name '*.whl' -print -quit)"; \
	if [ -z "$$wheel" ]; then \
		echo "No wheel found after build."; \
		exit 1; \
	fi; \
	unzip -l "$$wheel" | grep -q "$(PACKAGE)/py.typed"; \
	echo "✅ Wheel contains $(PACKAGE)/py.typed"
	$(MAKE) install-wheel

# ============================================
# 🧼 CLEANUP
# --------------------------------------------

.PHONY: clean clean-build clean-cache clean-coverage

clean: clean-build clean-cache clean-coverage ## Remove generated project files

clean-build: ## Remove package build artifacts
	rm -rf \
		$(BUILD_DIR) \
		$(DIST_DIR) \
		*.egg-info \
		src/*.egg-info

clean-cache: ## Remove Python and tool caches
	find . -type d \
		\( \
			-name "__pycache__" \
			-o -name ".pytest_cache" \
			-o -name ".ruff_cache" \
			-o -name ".mypy_cache" \
		\) \
		-prune \
		-exec rm -rf {} +

clean-coverage: ## Remove coverage output
	rm -rf \
		.coverage \
		.coverage.* \
		coverage.xml \
		htmlcov

# ============================================
# 🌲 FILE TREE / INSPECTION
# --------------------------------------------

.PHONY: tree

tree: ## List files under <folder>: make tree [folder=<folder>]
	@folder="$(folder)"; \
	if [ -z "$$folder" ]; then \
		folder="."; \
	fi; \
	folder="$${folder%/}"; \
	target="./$$folder"; \
	echo "📂 Listing files in: $$target"; \
	find "$$target" -type f \
		-not -path "*/.git/*" \
		-not -path "*/data/*" \
		-not -path "*/locale/*" \
		-not -path "*/node_modules/*" \
		-not -path "*/fixtures/*" \
		-not -path "*/*_cache/*" \
		-not -path "*/htmlcov/*" \
		-not -path "*/staticfiles/*" \
		-not -path "*/migrations/*" \
		-not -path "*/.venv/*" \
		-not -path "*/venv/*" \
		-not -path "*/dist/*" \
		-not -path "*/build/*" \
		-not -path "*/.hypothesis/*" \
		-not -path "*/.mypy_cache/*" \
		-not -path "*/.ruff_cache/*" \
		-not -path "*/.pytest_cache/*" \
		-not -path "*/__pycache__/*" \
		-not -path "*.egg-info/*" \
		-not -name ".coverage" \
		-not -name ".coverage.*" \
		-not -name "coverage.xml" \
		-not -name "*.pyc" \
		-not -name "*.pyo" \
		-not -name "*.DS_Store" \
		| sed 's|^\./||' \
		| sort

# ============================================
# 🧩 HELP
# --------------------------------------------

.PHONY: help

help: ## Show this help
	@echo "Available make targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?##"} {printf "  %-22s %s\n", $$1, $$2}'
