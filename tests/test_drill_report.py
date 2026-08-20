# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Tests for the DR evidence report semantic contract."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_drill_report", ROOT / "tools" / "validate_drill_report.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def valid_report() -> dict[str, object]:
    return {
        "schema_version": 2,
        "drill_id": "staging-gke-20260820",
        "drill_type": "gke-reconstruction",
        "scope": "staging recovery exercise",
        "environment": "staging",
        "operators": [
            {"identity": "primary-operator", "role": "primary"},
            {"identity": "observer-operator", "role": "observer"},
        ],
        "source_revisions": {"mindclade/gitops": "1" * 40},
        "started_at": "2026-08-20T12:00:00Z",
        "ended_at": "2026-08-20T12:30:00Z",
        "result": "pass",
        "objectives": {"rpo_seconds": 3600, "rto_seconds": 3600},
        "recovery_point": {"description": "last replicated state", "observed_at": "2026-08-20T11:45:00Z", "rpo_seconds": 900},
        "recovery_time_seconds": 1800,
        "success_criteria": ["staging service health checks pass"],
        "abort_conditions": ["production scope is selected"],
        "evidence": [{"uri": "gs://evidence/drills/log.txt", "sha256": "2" * 64, "classification": "restricted"}],
        "failures": [],
        "corrective_actions": [],
        "next_drill_at": "2026-11-20T12:00:00Z",
    }


class DrillReportTests(unittest.TestCase):
    def test_valid_pass_report(self) -> None:
        self.assertEqual([], VALIDATOR.validate(valid_report()))

    def test_same_operator_is_rejected(self) -> None:
        report = valid_report()
        report["operators"][1]["identity"] = "primary-operator"  # type: ignore[index]
        self.assertIn("operator identities must be distinct", VALIDATOR.validate(report))

    def test_pass_cannot_miss_rto(self) -> None:
        report = valid_report()
        report["recovery_time_seconds"] = 7200
        self.assertIn("observed RTO exceeds the objective", VALIDATOR.validate(report))

    def test_failure_requires_corrective_action(self) -> None:
        report = valid_report()
        report["result"] = "fail"
        report["failures"] = ["cluster did not recover"]
        self.assertIn("a partial or failed drill must have an open corrective action", VALIDATOR.validate(report))


if __name__ == "__main__":
    unittest.main()
