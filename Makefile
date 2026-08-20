PYTHON ?= python3
ACTIONLINT ?= actionlint
YAMLLINT ?= yamllint

.PHONY: validate lint contracts pins release-readiness repository-home validate-production-contract

validate: lint contracts pins release-readiness repository-home validate-production-contract
	$(PYTHON) tools/validate_repo.py

lint:
	$(ACTIONLINT) -config-file .github/actionlint.yaml .github/workflows/*.yml
	$(YAMLLINT) --strict .

contracts:
	$(PYTHON) tools/check_workflow_contracts.py

pins:
	$(PYTHON) tools/validate_action_pins.py

release-readiness:
	$(PYTHON) tools/validate_release_readiness.py

repository-home:
	$(PYTHON) actions/validate-repository-home/validate.py --root .
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

validate-production-contract:
	$(PYTHON) scripts/validate-production-contract.py
