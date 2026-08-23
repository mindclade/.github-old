#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "validate_evidence_contracts.py"
SPEC = importlib.util.spec_from_file_location("validate_evidence_contracts", MODULE_PATH)
assert SPEC and SPEC.loader
contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contracts)


class EvidenceContractsTest(unittest.TestCase):
    def test_canonical_contracts_validate(self) -> None:
        self.assertEqual(contracts.validate(), [])

    def test_current_deployment_bundle_requires_v2_provenance(self) -> None:
        schema = contracts.load("deployment-bundle.schema.json")
        schema["required"].remove("workflow_release_provenance")
        self.assertIn(
            "deployment-bundle.schema.json does not require its exact versioned field set",
            contracts.validate_deployment_schema(
                "deployment-bundle.schema.json", schema
            ),
        )

    def test_historical_schema_cannot_claim_the_current_version(self) -> None:
        schema = contracts.load("deployment-bundle-v1.schema.json")
        schema["properties"]["schema_version"]["const"] = (
            "mindclade.dev/deployment-bundle/v2"
        )
        self.assertIn(
            "deployment-bundle-v1.schema.json does not bind mindclade.dev/deployment-bundle/v1",
            contracts.validate_deployment_schema(
                "deployment-bundle-v1.schema.json", schema
            ),
        )

    def test_current_deployment_bundle_rejects_duplicate_release_digests(self) -> None:
        schema = json.loads(
            json.dumps(contracts.load("deployment-bundle.schema.json"))
        )
        del schema["properties"]["release_digests"]["uniqueItems"]
        self.assertIn(
            "deployment-bundle.schema.json must reject duplicate release digests",
            contracts.validate_deployment_schema(
                "deployment-bundle.schema.json", schema
            ),
        )


if __name__ == "__main__":
    unittest.main()
