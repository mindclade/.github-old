PYTHON ?= python3
ACTIONLINT ?= actionlint
YAMLLINT ?= yamllint

<<<<<<< HEAD
.PHONY: validate lint contracts pins release-readiness repository-home validate-production-contract
||||||| parent of 0ed0a1a (feat(ci): harden enterprise workflow platform)
.PHONY: validate lint contracts pins validate-production-contract
=======
.PHONY: validate lint contracts pins repository-home validate-production-contract
>>>>>>> 0ed0a1a (feat(ci): harden enterprise workflow platform)

<<<<<<< HEAD
validate: lint contracts pins release-readiness repository-home validate-production-contract
||||||| parent of 0ed0a1a (feat(ci): harden enterprise workflow platform)
validate: lint contracts pins validate-production-contract
=======
validate: lint contracts pins repository-home validate-production-contract
>>>>>>> 0ed0a1a (feat(ci): harden enterprise workflow platform)
	$(PYTHON) tools/validate_repo.py

lint:
	$(ACTIONLINT) -config-file .github/actionlint.yaml .github/workflows/*.yml
	$(YAMLLINT) --strict .

contracts:
	$(PYTHON) tools/check_workflow_contracts.py

pins:
	$(PYTHON) tools/validate_action_pins.py

<<<<<<< HEAD
release-readiness:
	$(PYTHON) tools/validate_release_readiness.py

||||||| parent of 0ed0a1a (feat(ci): harden enterprise workflow platform)
=======
>>>>>>> 0ed0a1a (feat(ci): harden enterprise workflow platform)
repository-home:
	$(PYTHON) actions/validate-repository-home/validate.py --root .
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

validate-production-contract:
	$(PYTHON) scripts/validate-production-contract.py
