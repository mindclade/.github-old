PYTHON ?= python3
ACTIONLINT ?= actionlint
YAMLLINT ?= yamllint

.PHONY: validate lint contracts release-spec pins repository-home validate-production-contract

validate: lint contracts release-spec pins repository-home validate-production-contract
	$(PYTHON) tools/validate_repo.py

lint:
	$(ACTIONLINT) -config-file .github/actionlint.yaml .github/workflows/*.yml
	$(YAMLLINT) --strict .

contracts:
	$(PYTHON) tools/check_workflow_contracts.py

release-spec:
	$(PYTHON) tools/validate-release-spec.py contracts/releases/v5.0.0.json

pins:
	$(PYTHON) tools/validate_action_pins.py

repository-home:
	$(PYTHON) actions/validate-repository-home/validate.py --root .
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

validate-production-contract:
	$(PYTHON) scripts/validate-production-contract.py
