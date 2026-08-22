#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import re
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "select_policy_bundle_run.py"
WORKFLOW = ROOT / ".github" / "workflows" / "synchronize-policy-bundle.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("select_policy_bundle_run", TOOL)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


selector = load_module()


class PolicyBundleSynchronizationTest(unittest.TestCase):
    source_commit = "a" * 40

    def test_selects_latest_matching_run_across_paginated_pages(self) -> None:
        pages = [
            {
                "total_count": 3,
                "workflow_runs": [
                    {"id": 10, "run_number": 10, "head_sha": self.source_commit},
                    {"id": 11, "run_number": 11, "head_sha": "b" * 40},
                ],
            },
            {
                "total_count": 3,
                "workflow_runs": [
                    {"id": 13, "run_number": 13, "head_sha": self.source_commit}
                ],
            },
        ]
        self.assertEqual(selector.select_run_id(pages, self.source_commit), 13)

    def test_rejects_missing_ambiguous_or_malformed_runs(self) -> None:
        cases = [
            ([{"workflow_runs": []}], "publication_run_not_found"),
            (
                [
                    {
                        "workflow_runs": [
                            {"id": 1, "run_number": 4, "head_sha": self.source_commit},
                            {"id": 2, "run_number": 4, "head_sha": self.source_commit},
                        ]
                    }
                ],
                "publication_run_ambiguous",
            ),
            ([{"workflow_runs": [{"id": True, "run_number": 1, "head_sha": self.source_commit}]}], "workflow_run_invalid"),
            ([{"total_count": 1}], "workflow_runs_missing"),
        ]
        for pages, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(
                selector.SelectionError, message
            ):
                selector.select_run_id(pages, self.source_commit)

    def test_loader_rejects_duplicate_keys_and_non_paginated_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = Path(directory) / "runs.json"
            payload.write_text('[{"workflow_runs": [], "workflow_runs": []}]', encoding="utf-8")
            with self.assertRaisesRegex(selector.SelectionError, "duplicate_json_key"):
                selector.load_pages(payload)

            payload.write_text(json.dumps({"workflow_runs": []}), encoding="utf-8")
            with self.assertRaisesRegex(selector.SelectionError, "workflow_run_pages_invalid"):
                selector.load_pages(payload)

    def test_workflow_invokes_the_selector_with_exact_inputs(self) -> None:
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["synchronize"]["steps"]
        publication = [step for step in steps if step.get("id") == "publication"]
        self.assertEqual(len(publication), 1)
        script = publication[0]["run"]
        active = "\n".join(
            line for line in script.splitlines() if not line.lstrip().startswith("#")
        ).replace("\\\n", " ")
        invocation = re.findall(
            r'run_id="\$\(\s*(python3 source/tools/select_policy_bundle_run\.py\s+'
            r'--runs "\$runs"\s+--source-commit "\$source_commit")\s*\)"',
            active,
        )
        self.assertEqual(len(invocation), 1)
        self.assertEqual(
            shlex.split(invocation[0]),
            [
                "python3",
                "source/tools/select_policy_bundle_run.py",
                "--runs",
                "$runs",
                "--source-commit",
                "$source_commit",
            ],
        )


if __name__ == "__main__":
    unittest.main()
