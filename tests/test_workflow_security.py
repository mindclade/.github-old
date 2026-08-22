#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def run_scripts(text: str) -> list[str]:
    lines = text.splitlines()
    scripts: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*(.*)$", lines[index])
        if match is None:
            index += 1
            continue
        indentation, body = match.groups()
        if body not in {"|", ">"}:
            scripts.append(body)
            index += 1
            continue
        start = index + 1
        index = start
        while index < len(lines):
            line = lines[index]
            if line and len(line) - len(line.lstrip()) <= len(indentation):
                break
            index += 1
        scripts.append("\n".join(lines[start:index]))
    return scripts


class WorkflowSecurityTests(unittest.TestCase):
    def test_uv_inputs_are_not_interpolated_into_shell_scripts(self) -> None:
        text = (WORKFLOWS / "reusable-uv-ci.yml").read_text(encoding="utf-8")
        scripts = "\n".join(run_scripts(text))

        self.assertNotIn("${{ inputs.packages }}", scripts)
        self.assertNotIn("${{ inputs.pytest-args }}", scripts)
        self.assertEqual(text.count("PACKAGES: ${{ inputs.packages }}"), 2)
        self.assertEqual(text.count("PYTEST_ARGS: ${{ inputs.pytest-args }}"), 1)
        self.assertIn('read -r -a package_args <<< "${PACKAGES:-}"', scripts)
        self.assertIn('read -r -a pytest_args <<< "${PYTEST_ARGS:-}"', scripts)

    def test_qualification_image_ref_is_not_interpolated_into_shell(self) -> None:
        text = (WORKFLOWS / "reusable-arc-oci-qualify.yml").read_text(
            encoding="utf-8"
        )
        scripts = "\n".join(run_scripts(text))

        self.assertNotIn("${{ inputs.image-ref }}", scripts)
        self.assertEqual(
            text.count("EXPECTED_IMAGE_REF: ${{ inputs.image-ref }}"),
            2,
        )
        self.assertEqual(scripts.count('--expected-image-ref "$EXPECTED_IMAGE_REF"'), 2)

    def test_dependency_review_covers_merge_queue_and_fails_closed(self) -> None:
        text = (WORKFLOWS / "required-security-baseline.yml").read_text(
            encoding="utf-8"
        )
        dependency_review = text.split("\n  dependency-review:\n", maxsplit=1)[1].split(
            "\n  action-pin-policy:\n", maxsplit=1
        )[0]
        verdict = text.split("\n  verdict:\n", maxsplit=1)[1]

        self.assertNotRegex(dependency_review, r"(?m)^    if:")
        self.assertIn("github.event.merge_group.base_sha", dependency_review)
        self.assertIn("github.event.merge_group.head_sha", dependency_review)
        self.assertNotIn("success|skipped", verdict)
        self.assertIn('[ "${DEPENDENCY_REVIEW}" != "success" ]', verdict)

    def test_actionlint_does_not_allow_retired_attest_runner(self) -> None:
        text = (ROOT / ".github" / "actionlint.yaml").read_text(encoding="utf-8")
        self.assertNotIn("mindclade-arc-qualify-attest", text)


if __name__ == "__main__":
    unittest.main()
