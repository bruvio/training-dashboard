# Employee Simulation System Makefile
# All tools run from a local virtualenv to avoid PEP 668 issues.
# Docformatter now runs per-file, collects failures, and reports them without stopping other fixes.

VENV ?= venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Tool binaries from the venv
BLACK := $(VENV)/bin/black
FLAKE8 := $(VENV)/bin/flake8
RUFF := $(VENV)/bin/ruff
ISORT := $(VENV)/bin/isort
DOCFORMATTER := $(VENV)/bin/docformatter
AUTOFLAKE := $(VENV)/bin/autoflake
PYTEST := $(VENV)/bin/pytest
COVERAGE := $(VENV)/bin/coverage
PIP_COMPILE := $(VENV)/bin/pip-compile

# Shared flags
EXCLUDES := .venv,venv,__pycache__,artifacts,images,htmlcov,tests,key-value-conf.py,test_*.py
RUFF_FLAGS := --line-length 120 --extend-exclude $(EXCLUDES) --force-exclude
FLAKE8_FLAGS := --exclude $(EXCLUDES)
DOCFORMATTER_FLAGS := --wrap-summaries 120 --wrap-descriptions 120 --pre-summary-newline --make-summary-multi-line --close-quotes-on-newline

# File list for formatters (prefer git, fallback to find)
define PY_SOURCES_CMD
git ls-files '*.py' 2>/dev/null || find . -type f -name '*.py' \
  -not -path './$(VENV)/*' -not -path './.venv/*' \
  -not -path './tests/*' -not -path './artifacts/*' \
  -not -path './images/*' -not -path './htmlcov/*'
endef

.PHONY: help
help:
	@echo "Employee Simulation System"
	@echo "Available targets:"
	@echo "  bootstrap           - Create venv and install dev tools"
	@echo "  venv                - Create local virtualenv at '$(VENV)'"
	@echo "  tools-install       - Install dev tools into venv"
	@echo "  black               - Format code with black"
	@echo "  black-check         - Check code formatting with black"
	@echo "  flake               - Run flake8 linting"
	@echo "  pytest              - Run unit tests (verbose)"
	@echo "  pip-compile         - Compile requirements"
	@echo "  pip-upgrade         - Upgrade requirements"
	@echo "  run                 - Run the application"
	@echo "  analyze-individual  - Run individual employee analysis (set EMPLOYEE_DATA)"
	@echo "  clean               - Clean temporary files"
	@echo "  coverage            - Coverage report"
	@echo "  unit                - Run all tests and generate coverage"
	@echo "  lint                - Run ruff + flake8 (no fixes) respecting excludes"
	@echo "  lint-fix            - Auto-fix lint (ruff+isort+docformatter+black) then flake8"
	@echo "  format              - Apply isort+docformatter+black (no linting)"
	@echo "  docformat           - Format docstrings (per-file, shows failures)"
	@echo "  autoflake-fix       - Remove unused imports/vars with autoflake (optional)"

# ---------- Environment setup ----------
.PHONY: bootstrap
bootstrap: venv tools-install ## Create venv and install all tools

.PHONY: venv
venv:
	@test -d "$(VENV)" || python3 -m venv "$(VENV)"
	@echo "✅ Virtualenv ensured at $(VENV)"

.PHONY: tools-install
tools-install: venv
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --upgrade ruff isort docformatter black autoflake flake8 coverage pip-tools
	@echo "✅ Dev tools installed into $(VENV)"

# ---------- Formatting & Linting ----------
.PHONY: black
black:
	$(BLACK) --line-length=120 .

.PHONY: black-check
black-check:
	$(BLACK) --line-length=120 --check .

.PHONY: flake
flake:
	$(FLAKE8) $(FLAKE8_FLAGS) .

.PHONY: pytest
pytest:
	$(PYTEST) -vvv -rPxwef

.PHONY: pip-compile
pip-compile:
	$(PIP_COMPILE) requirements.txt
	$(PIP_COMPILE) requirements-test.txt

.PHONY: pip-upgrade
pip-upgrade:
	$(PIP_COMPILE) -U requirements.txt
	$(PIP_COMPILE) -U requirements-test.txt

.PHONY: run
run:
	$(PYTHON) employee_simulation_orchestrator.py --scenario basic --population-size 100

.PHONY: analyze-individual
analyze-individual:
	@if [ -z "$(EMPLOYEE_DATA)" ]; then \
		echo "Error: EMPLOYEE_DATA is required"; \
		echo "Example: make analyze-individual EMPLOYEE_DATA='level:5,salary:80692.5,performance:Exceeding'"; \
		exit 1; \
	fi
	$(PYTHON) employee_simulation_orchestrator.py --scenario individual --employee-data "$(EMPLOYEE_DATA)"

.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

.PHONY: coverage
coverage:  ## coverage report
	$(COVERAGE) report --fail-under 5
	$(COVERAGE) html -i

.PHONY: coverage-report
coverage-report:  ## Enhanced coverage report for 91% target
	$(COVERAGE) report --show-missing --fail-under 91
	$(COVERAGE) html -d htmlcov --title="Coverage Report - 91% Target"
	$(COVERAGE) xml -o coverage.xml

.PHONY: pytest-ci
pytest-ci:  ## Run tests with coverage for CI
	$(PYTEST) -vvv -rPxwef -m "not auth" --tb=short --cov=app --cov-report=xml --cov-report=html --cov-report=term

.PHONY: unit
unit: | pytest coverage  ## run all tests and test coverage

# ---- Lint flows ----
.PHONY: lint
lint:
	$(RUFF) check . $(RUFF_FLAGS)
	$(FLAKE8) $(FLAKE8_FLAGS) .

.PHONY: lint-fix
lint-fix:
	# 1) Broad lint autofix (enable unsafe fixes to remove unused assignments/imports)
	$(RUFF) check . --fix --unsafe-fixes $(RUFF_FLAGS)
	# 2) Canonicalize imports (fixes I101 and friends)
	$(ISORT) .
	# 3) Docstrings per-file (fix D209 and wrapping); collect failures and continue
	@fails=(); \
	files="$$( $(PY_SOURCES_CMD) )"; \
	for f in $$files; do \
		$(DOCFORMATTER) -i $(DOCFORMATTER_FLAGS) "$$f" || fails+=("$$f"); \
	done; \
	if [ $${#fails[@]} -gt 0 ]; then \
		echo "❌ docformatter failed on the following files:"; \
		for f in "$${fails[@]}"; do echo "   - $$f"; done; \
		exit 3; \
	fi
	# 4) Final formatting pass (also clears W291 trailing whitespace)
	$(BLACK) --line-length=120 .
	# 5) Verify with your existing flake8 config (same excludes)
	$(FLAKE8) $(FLAKE8_FLAGS) .

# ---- Simple format-only helpers ----
.PHONY: format
format:
	$(ISORT) .
	@fails=(); \
	files="$$( $(PY_SOURCES_CMD) )"; \
	for f in $$files; do \
		$(DOCFORMATTER) -i $(DOCFORMATTER_FLAGS) "$$f" || fails+=("$$f"); \
	done; \
	if [ $${#fails[@]} -gt 0 ]; then \
		echo "❌ docformatter failed on the following files:"; \
		for f in "$${fails[@]}"; do echo "   - $$f"; done; \
		exit 3; \
	fi
	$(BLACK) --line-length=120 .

.PHONY: docformat
docformat:
	@fails=(); \
	files="$$( $(PY_SOURCES_CMD) )"; \
	for f in $$files; do \
		$(DOCFORMATTER) -i $(DOCFORMATTER_FLAGS) "$$f" || fails+=("$$f"); \
	done; \
	if [ $${#fails[@]} -gt 0 ]; then \
		echo "❌ docformatter failed on the following files:"; \
		for f in "$${fails[@]}"; do echo "   - $$f"; done; \
		exit 3; \
	fi

.PHONY: ruff
ruff:
	$(RUFF) check . $(RUFF_FLAGS)

.PHONY: isort
isort:
	$(ISORT) .

.PHONY: autoflake-fix
autoflake-fix:
	$(AUTOFLAKE) -r -i \
	  --remove-all-unused-imports \
	  --remove-unused-variables \
	  --expand-star-imports \
	  --ignore-init-module-imports \
	  .

.DEFAULT_GOAL := help
