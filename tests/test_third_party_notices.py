#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "third_party_notices.py"
SPEC = importlib.util.spec_from_file_location("third_party_notices", MODULE_PATH)
assert SPEC and SPEC.loader
third_party_notices = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(third_party_notices)


class ThirdPartyNoticesTests(unittest.TestCase):
    def test_repository_notice_is_deterministic_and_current(self) -> None:
        contract = third_party_notices.load_contract(
            ROOT / "contracts" / "third-party-materials.json"
        )
        materials = third_party_notices.validate_contract(contract, ROOT)
        rendered = third_party_notices.render(contract, materials)
        self.assertEqual(
            rendered,
            (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8"),
        )

    def test_paths_cannot_escape_the_repository(self) -> None:
        with self.assertRaisesRegex(third_party_notices.NoticeError, "normalized relative"):
            third_party_notices._safe_path(ROOT, "../escape", "fixture")

    def test_spdx_package_requires_reviewed_notice_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spdx = Path(directory) / "sbom.spdx.json"
            spdx.write_text(
                json.dumps(
                    {
                        "packages": [
                            {"SPDXID": "SPDXRef-Package-example", "name": "example"}
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                third_party_notices.NoticeError, "lacks reviewed notice metadata"
            ):
                third_party_notices.validate_spdx_coverage([spdx], [])


if __name__ == "__main__":
    unittest.main()
