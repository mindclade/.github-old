#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


estate_status = module("estate_status")
ref_janitor = module("ref_janitor")


class FakeEstateClient:
    def get(self, path: str, allow_not_found: bool = False):
        if path.endswith("/branches/main"):
            return {"commit": {"sha": "a" * 40}}
        if "/check-runs" in path:
            return {"check_runs": [{"status": "completed", "conclusion": "success"}]}
        if "/actions/runs" in path:
            return {"workflow_runs": [{"name": "CI", "status": "completed", "conclusion": "success", "html_url": "https://example.test"}]}
        if path.startswith("/repos/"):
            return {"default_branch": "main", "archived": False}
        raise AssertionError(path)

    def paginate(self, path: str):
        if "/pulls?" in path:
            return [{"draft": False}]
        if "/heads/" in path:
            return [{"ref": "refs/heads/main"}, {"ref": "refs/heads/feature"}]
        if "/tags/" in path:
            return [{"ref": "refs/tags/v1.0.0"}]
        raise AssertionError(path)


class FakeJanitorClient:
    def __init__(self, tag_ahead: int = 0) -> None:
        self.deleted: list[str] = []
        self.tag_ahead = tag_ahead

    def get(self, path: str, allow_not_found: bool = False):
        if path.endswith("/repos/mindclade/example"):
            return {"default_branch": "main"}
        if "/compare/main...merged" in path:
            return {"ahead_by": 0}
        if f"/compare/main...{'b' * 40}" in path:
            return {"ahead_by": 0}
        if f"/compare/main...{'c' * 40}" in path:
            return {"ahead_by": self.tag_ahead}
        if "/git/ref/heads/merged" in path:
            return {"object": {"sha": "b" * 40}}
        if "/git/ref/tags/scratch" in path:
            return {"object": {"sha": "c" * 40}}
        if "/commits/" in path:
            return {"commit": {"committer": {"date": "2026-01-01T00:00:00Z"}}}
        if "/releases/tags/" in path and allow_not_found:
            return None
        raise AssertionError(path)

    def paginate(self, path: str):
        if "/pulls?" in path:
            return []
        if "/heads/" in path:
            return [
                {"ref": "refs/heads/main", "object": {"type": "commit", "sha": "a" * 40}},
                {"ref": "refs/heads/merged", "object": {"type": "commit", "sha": "b" * 40}},
            ]
        if "/tags/" in path:
            return [{"ref": "refs/tags/scratch", "object": {"type": "commit", "sha": "c" * 40}}]
        raise AssertionError(path)

    def delete(self, path: str) -> None:
        self.deleted.append(path)


class EstateAutomationTest(unittest.TestCase):
    def test_dashboard_aggregates_green_state(self) -> None:
        report = estate_status.collect(FakeEstateClient(), "mindclade", estate_status.REPOSITORIES)
        self.assertEqual(report["summary"]["green"], 7)
        self.assertEqual(report["summary"]["open_pull_requests"], 7)
        self.assertIn("mindclade-internal-monorepo", estate_status.markdown(report))

    def test_janitor_only_deletes_merged_and_unauthorized_retained_refs(self) -> None:
        client = FakeJanitorClient()
        config = {
            "schema_version": 1,
            "organization": "mindclade",
            "repositories": {
                "example": {
                    "branch_retention_days": 30,
                    "tag_retention_days": 30,
                    "protected_branches": ["main"],
                    "protected_branch_prefixes": ["automation/"],
                    "allowed_tag_patterns": ["^v[0-9]+\\.[0-9]+\\.[0-9]+$"],
                }
            },
        }
        report = ref_janitor.plan(client, config, datetime(2026, 8, 22, tzinfo=timezone.utc))
        self.assertEqual(report["summary"], {"branch_deletions": 1, "tag_deletions": 1})
        ref_janitor.execute(client, report)
        self.assertEqual(
            client.deleted,
            [
                "/repos/mindclade/example/git/refs/heads/merged",
                "/repos/mindclade/example/git/refs/tags/scratch",
            ],
        )

    def test_janitor_preserves_a_tag_that_is_the_last_unique_ref(self) -> None:
        client = FakeJanitorClient(tag_ahead=1)
        config = {
            "schema_version": 1,
            "organization": "mindclade",
            "repositories": {
                "example": {
                    "branch_retention_days": 30,
                    "tag_retention_days": 30,
                    "protected_branches": ["main"],
                    "protected_branch_prefixes": ["automation/"],
                    "allowed_tag_patterns": ["^v[0-9]+\\.[0-9]+\\.[0-9]+$"],
                }
            },
        }
        report = ref_janitor.plan(client, config, datetime(2026, 8, 22, tzinfo=timezone.utc))
        tag = report["repositories"][0]["tags"][0]
        self.assertEqual((tag["decision"], tag["reason"]), ("preserve", "contains_unique_commits"))

    def test_janitor_rejects_a_ref_that_moves_after_planning(self) -> None:
        client = FakeJanitorClient()
        report = {
            "schema_version": 1,
            "organization": "mindclade",
            "repositories": [
                {
                    "repository": "example",
                    "default_branch": "main",
                    "branches": [{"name": "merged", "sha": "f" * 40, "decision": "delete"}],
                    "tags": [],
                }
            ],
        }
        with self.assertRaises(ValueError):
            ref_janitor.execute(client, report)


if __name__ == "__main__":
    unittest.main()
