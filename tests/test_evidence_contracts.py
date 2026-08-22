#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
