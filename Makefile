.PHONY: validate contracts pins

validate: contracts pins validate-production-contract
	python3 tools/validate_repo.py

contracts:
	python3 tools/check_workflow_contracts.py

pins:
	python3 tools/validate_action_pins.py

.PHONY: validate-production-contract
validate-production-contract:
	python3 scripts/validate-production-contract.py
