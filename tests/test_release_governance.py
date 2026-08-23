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
        self.tag_protection = load("tag-protection.json")

    def validate(self) -> None:
        release_governance.validate_snapshot(
            self.environments,
            self.rulesets,
            self.ruleset,
            self.tag_protection,
            103,
        )

    def test_qualified_snapshot_passes(self) -> None:
        self.validate()

    def test_environment_admin_bypass_is_rejected(self) -> None:
        self.environments["workflow-release-platform"]["can_admins_bypass"] = True
        with self.assertRaisesRegex(
            release_governance.GovernanceError, "administrator"
        ):
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
        with self.assertRaisesRegex(
            release_governance.GovernanceError, "protected-branches"
        ):
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

    def test_tag_protection_rejects_missing_rule_or_bypass(self) -> None:
        self.tag_protection["rules"] = self.tag_protection["rules"][:-1]
        with self.assertRaisesRegex(release_governance.GovernanceError, "four"):
            self.validate()

        self.tag_protection = load("tag-protection.json")
        self.tag_protection["bypass_actors"] = [
            {"actor_id": 103, "actor_type": "Team", "bypass_mode": "always"}
        ]
        with self.assertRaisesRegex(release_governance.GovernanceError, "no bypass"):
            self.validate()

    def test_tag_protection_rejects_mutable_pattern(self) -> None:
        pattern = next(
            rule
            for rule in self.tag_protection["rules"]
            if rule["type"] == "tag_name_pattern"
        )
        pattern["parameters"]["pattern"] = "^v.*$"
        with self.assertRaisesRegex(release_governance.GovernanceError, "SemVer"):
            self.validate()

    def test_snapshot_is_not_mutated(self) -> None:
        before = copy.deepcopy(self.environments)
        self.validate()
        self.assertEqual(self.environments, before)

    def test_immutable_releases_require_organization_enforcement(self) -> None:
        release_governance.validate_immutable_releases(
            {"enabled": True, "enforced_by_owner": True}
        )
        with self.assertRaisesRegex(release_governance.GovernanceError, "enabled"):
            release_governance.validate_immutable_releases(
                {"enabled": False, "enforced_by_owner": False}
            )
        with self.assertRaisesRegex(release_governance.GovernanceError, "organization"):
            release_governance.validate_immutable_releases(
                {"enabled": True, "enforced_by_owner": False}
            )

    def test_release_approval_history_requires_distinct_team_members(self) -> None:
        approvals = [
            {
                "state": "approved",
                "environments": [{"name": "workflow-release-platform"}],
                "user": {"id": 201, "login": "platform-reviewer"},
            },
            {
                "state": "approved",
                "environments": [{"name": "workflow-release-security"}],
                "user": {"id": 202, "login": "security-reviewer"},
            },
        ]
        approved = release_governance.validate_approval_history(
            approvals, "release-operator"
        )
        self.assertEqual(
            {reviewer["login"] for reviewer in approved.values()},
            {"platform-reviewer", "security-reviewer"},
        )

        approvals[1]["user"] = approvals[0]["user"]
        with self.assertRaisesRegex(release_governance.GovernanceError, "distinct"):
            release_governance.validate_approval_history(approvals, "release-operator")

    def test_release_approval_history_rejects_dispatcher_or_missing_approval(
        self,
    ) -> None:
        approvals = [
            {
                "state": "approved",
                "environments": [{"name": "workflow-release-platform"}],
                "user": {"id": 201, "login": "release-operator"},
            }
        ]
        with self.assertRaisesRegex(release_governance.GovernanceError, "dispatcher"):
            release_governance.validate_approval_history(approvals, "release-operator")

        approvals[0]["user"] = {"id": 201, "login": "platform-reviewer"}
        with self.assertRaisesRegex(release_governance.GovernanceError, "exactly one"):
            release_governance.validate_approval_history(approvals, "release-operator")

    def test_release_approval_reviewer_requires_active_team_membership(self) -> None:
        release_governance.validate_team_membership(
            {"state": "active", "role": "member"}, "security", "reviewer"
        )
        with self.assertRaisesRegex(
            release_governance.GovernanceError, "active member"
        ):
            release_governance.validate_team_membership(
                {"state": "pending", "role": "member"}, "security", "reviewer"
            )

    def test_pagination_cannot_forward_the_token_to_another_origin(self) -> None:
        client = release_governance.GitHubClient(
            token="fixture", api_url="https://api.github.test"
        )
        with self.assertRaisesRegex(release_governance.GovernanceError, "origin"):
            client.get("https://attacker.invalid/rulesets")


if __name__ == "__main__":
    unittest.main()
