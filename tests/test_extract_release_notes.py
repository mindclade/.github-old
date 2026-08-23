# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "extract_release_notes", ROOT / "tools" / "extract_release_notes.py"
)
assert SPEC and SPEC.loader
NOTES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NOTES)


class ExtractReleaseNotesTests(unittest.TestCase):
    def test_extracts_only_the_exact_version_section(self) -> None:
        contents = "# Changelog\n\n## v5.0.0\n\n- exact\n\n## v4.0.0\n\n- old\n"
        self.assertEqual("- exact\n", NOTES.extract(contents, "v5.0.0"))

    def test_planned_suffix_does_not_match(self) -> None:
        contents = "# Changelog\n\n## v5.0.0 (planned; not published)\n\n- candidate\n"
        with self.assertRaisesRegex(NOTES.ReleaseNotesError, "exactly one exact"):
            NOTES.extract(contents, "v5.0.0")

    def test_empty_section_is_rejected(self) -> None:
        contents = "# Changelog\n\n## v5.0.0\n\n \n## v4.0.0\n\n- old\n"
        with self.assertRaisesRegex(NOTES.ReleaseNotesError, "no release notes"):
            NOTES.extract(contents, "v5.0.0")

    def test_duplicate_exact_section_is_rejected(self) -> None:
        contents = "## v5.0.0\n- first\n## v5.0.0\n- second\n"
        with self.assertRaisesRegex(NOTES.ReleaseNotesError, "exactly one exact"):
            NOTES.extract(contents, "v5.0.0")

    def test_prerelease_tag_is_rejected(self) -> None:
        with self.assertRaisesRegex(NOTES.ReleaseNotesError, "stable"):
            NOTES.extract("## v5.0.0-rc.1\n- candidate\n", "v5.0.0-rc.1")


if __name__ == "__main__":
    unittest.main()
