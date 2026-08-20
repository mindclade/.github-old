PYTHON ?= python3
ACTIONLINT ?= actionlint
YAMLLINT ?= yamllint

.PHONY: validate lint contracts pins validate-production-contract

validate: lint contracts pins validate-production-contract
	$(PYTHON) tools/validate_repo.py

lint:
	$(ACTIONLINT) -config-file .github/actionlint.yaml .github/workflows/*.yml
	$(YAMLLINT) --strict .

contracts:
	$(PYTHON) tools/check_workflow_contracts.py

pins:
	$(PYTHON) tools/validate_action_pins.py

validate-production-contract:
	$(PYTHON) scripts/validate-production-contract.py
