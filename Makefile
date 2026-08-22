PYTHON ?= python3
ACTIONLINT ?= actionlint
YAMLLINT ?= yamllint

.PHONY: validate lint contracts release-spec v4-release-readiness pins repository-home third-party-notices validate-production-contract

validate: lint contracts release-spec v4-release-readiness pins repository-home third-party-notices validate-production-contract
	$(PYTHON) tools/validate_repo.py

lint:
	$(ACTIONLINT) -config-file .github/actionlint.yaml .github/workflows/*.yml
	$(YAMLLINT) --strict .

contracts:
	$(PYTHON) tools/check_workflow_contracts.py

release-spec:
	$(PYTHON) tools/validate-release-spec.py contracts/releases/v5.0.0.json

v4-release-readiness:
	$(PYTHON) tools/validate_release_readiness.py

pins:
	$(PYTHON) tools/validate_action_pins.py

repository-home:
	$(PYTHON) actions/validate-repository-home/validate.py --root .
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

third-party-notices:
	$(PYTHON) tools/third_party_notices.py

validate-production-contract:
	$(PYTHON) scripts/validate-production-contract.py
