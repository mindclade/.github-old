#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "check_workflow_contracts.py"
SPEC = importlib.util.spec_from_file_location("check_workflow_contracts", MODULE_PATH)
assert SPEC and SPEC.loader
workflow_contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow_contracts)


class WorkflowContractTests(unittest.TestCase):
    def extract(self, source: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflow = root / ".github" / "workflows" / "reusable-fixture.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
            with mock.patch.object(workflow_contracts, "ROOT", root):
                return workflow_contracts.extract(workflow)

    def test_unquoted_on_and_inline_write_all_are_semantic(self) -> None:
        contract = self.extract(
            """
            name: Fixture
            on:
                workflow_call:
                    inputs:
                        attempts:
                            required: false
                            type: number
                            default: 3
                    secrets:
                        token:
                            required: true
                    outputs:
                        zeta:
                            description: ignored implementation detail
                        alpha:
                            description: ignored implementation detail
            permissions: write-all
            jobs:
                build:
                    runs-on: ubuntu-24.04
                    steps: []
            """
        )

        self.assertEqual(contract["permissions"], "write-all")
        self.assertEqual(contract["jobs"], ["build"])
        self.assertEqual(contract["outputs"], ["alpha", "zeta"])
        self.assertEqual(
            contract["inputs"],
            {"attempts": {"default": 3, "required": False, "type": "number"}},
        )
        self.assertEqual(contract["secrets"], {"token": {"required": True}})

    def test_mapping_and_scalar_job_permissions_are_preserved(self) -> None:
        contract = self.extract(
            """
            name: Fixture
            on:
              workflow_call:
            permissions: {id-token: write, contents: read}
            jobs:
              plan:
                runs-on: ubuntu-24.04
                permissions:
                  pull-requests: write
                  contents: read
              inspect:
                runs-on: ubuntu-24.04
                permissions: read-all
            """
        )

        self.assertEqual(
            contract["permissions"], {"contents": "read", "id-token": "write"}
        )
        self.assertEqual(
            contract["job_permissions"],
            {
                "inspect": "read-all",
                "plan": {"contents": "read", "pull-requests": "write"},
            },
        )

    def test_zero_job_level_permission_entries_remain_empty(self) -> None:
        contract = self.extract(
            """
            name: Fixture
            on:
              workflow_call:
            permissions:
              contents: read
            jobs:
              inspect:
                runs-on: ubuntu-24.04
                steps:
                  - run: |
                      printf '%s\\n' 'permissions: write-all'
            """
        )

        self.assertEqual(contract["job_permissions"], {})

    def test_invalid_permission_contracts_fail_closed(self) -> None:
        invalid_permissions = (
            "permissions: admin",
            "permissions:\n  contents: delete",
            "permissions:\n  unknown-scope: read",
        )
        for permissions in invalid_permissions:
            with self.subTest(permissions=permissions):
                with self.assertRaisesRegex(ValueError, "permissions"):
                    self.extract(
                        "name: Fixture\n"
                        "on:\n"
                        "  workflow_call:\n"
                        f"{permissions}\n"
                        "jobs:\n"
                        "  inspect:\n"
                        "    runs-on: ubuntu-24.04\n"
                    )

    def test_duplicate_yaml_keys_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate key 'contents'"):
            self.extract(
                """
                name: Fixture
                on:
                  workflow_call:
                permissions:
                  contents: read
                  contents: write
                jobs:
                  inspect:
                    runs-on: ubuntu-24.04
                """
            )

    def test_jobs_must_be_a_mapping(self) -> None:
        with self.assertRaisesRegex(ValueError, "jobs must be a mapping"):
            self.extract(
                """
                name: Fixture
                on:
                  workflow_call:
                permissions: read-all
                jobs: []
                """
            )


if __name__ == "__main__":
    unittest.main()
