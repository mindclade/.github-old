#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/release-governance"
MODULE_PATH = ROOT / "tools/verify_release_governance.py"
SPEC = importlib.util.spec_from_file_location("release_governance", MODULE_PATH)
assert SPEC and SPEC.loader
release_governance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_governance)


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ReleaseGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environments = {
            "workflow-release-platform": load("platform.json"),
            "workflow-release-security": load("security.json"),
        }
        self.rulesets = load("rulesets.json")
        self.ruleset = load("ruleset.json")

    def validate(self) -> None:
        release_governance.validate_snapshot(
            self.environments, self.rulesets, self.ruleset, 103
        )

    def test_qualified_snapshot_passes(self) -> None:
        self.validate()

    def test_environment_admin_bypass_is_rejected(self) -> None:
        self.environments["workflow-release-platform"]["can_admins_bypass"] = True
        with self.assertRaisesRegex(release_governance.GovernanceError, "administrator"):
            self.validate()

    def test_environment_self_review_is_rejected(self) -> None:
        self.environments["workflow-release-security"]["protection_rules"][1][
            "prevent_self_review"
        ] = False
        with self.assertRaisesRegex(release_governance.GovernanceError, "self-review"):
            self.validate()

    def test_custom_branch_policy_is_rejected(self) -> None:
        policy = self.environments["workflow-release-platform"][
            "deployment_branch_policy"
        ]
        policy["protected_branches"] = False
        policy["custom_branch_policies"] = True
        with self.assertRaisesRegex(release_governance.GovernanceError, "protected-branches"):
            self.validate()

    def test_wrong_or_shared_reviewer_is_rejected(self) -> None:
        entry = self.environments["workflow-release-security"]["protection_rules"][1][
            "reviewers"
        ][0]["reviewer"]
        entry["slug"] = "platform"
        entry["id"] = 101
        with self.assertRaises(release_governance.GovernanceError):
            self.validate()

    def test_evaluate_ruleset_is_rejected(self) -> None:
        self.rulesets[0]["enforcement"] = "evaluate"
        with self.assertRaisesRegex(release_governance.GovernanceError, "enforcement"):
            self.validate()

    def test_extra_or_missing_creation_rule_is_rejected(self) -> None:
        self.ruleset["rules"].append({"type": "update"})
        with self.assertRaisesRegex(release_governance.GovernanceError, "only"):
            self.validate()

    def test_non_release_bypass_is_rejected(self) -> None:
        self.ruleset["bypass_actors"][0]["actor_id"] = 999
        with self.assertRaisesRegex(release_governance.GovernanceError, "Release-team"):
            self.validate()

    def test_snapshot_is_not_mutated(self) -> None:
        before = copy.deepcopy(self.environments)
        self.validate()
        self.assertEqual(self.environments, before)

    def test_pagination_cannot_forward_the_token_to_another_origin(self) -> None:
        client = release_governance.GitHubClient(
            token="fixture", api_url="https://api.github.test"
        )
        with self.assertRaisesRegex(release_governance.GovernanceError, "origin"):
            client.get("https://attacker.invalid/rulesets")


if __name__ == "__main__":
    unittest.main()
