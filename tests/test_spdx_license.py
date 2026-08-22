# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "enrich_spdx_license", ROOT / "tools" / "enrich_spdx_license.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def base_document() -> dict[str, object]:
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "generated",
        "documentNamespace": "https://example.invalid/spdx/generated",
        "creationInfo": {
            "created": "2026-08-21T00:00:00Z",
            "creators": ["Tool: test"],
        },
        "packages": [
            {
                "name": "third-party-package",
                "SPDXID": "SPDXRef-Package-third-party",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "MIT",
                "licenseDeclared": "MIT",
                "copyrightText": "NOASSERTION",
            }
        ],
        "relationships": [],
    }


def contract() -> dict[str, str]:
    license_path = ROOT / "LICENSE"
    manifest_path = ROOT / "contracts" / "policy-bundle" / "manifest.json"
    bundle_version, manifest_digest, license_digest = MODULE.policy_identity(
        manifest_path, license_path
    )
    return {
        "license_text": license_path.read_text(encoding="utf-8"),
        "license_digest": license_digest,
        "repository": "mindclade/example",
        "source_sha": "a" * 40,
        "artifact_name": "us-central1-docker.pkg.dev/project/repository/example",
        "artifact_digest": "sha256:" + "b" * 64,
        "bundle_version": bundle_version,
        "manifest_digest": manifest_digest,
    }


class SpdxLicenseTests(unittest.TestCase):
    def test_enrichment_is_exact_idempotent_and_preserves_third_party_package(self) -> None:
        document = MODULE.enrich_document(base_document(), **contract())
        MODULE.validate_document(document, **contract())
        self.assertEqual(
            MODULE.enrich_document(copy.deepcopy(document), **contract()), document
        )
        extracted = document["hasExtractedLicensingInfos"]
        self.assertEqual(extracted[0]["licenseId"], MODULE.LICENSE_ID)
        self.assertEqual(extracted[0]["extractedText"], (ROOT / "LICENSE").read_text())
        self.assertTrue(
            any(item.get("SPDXID") == "SPDXRef-Package-third-party" for item in document["packages"])
        )
        package = next(
            item for item in document["packages"] if item.get("SPDXID") == MODULE.PACKAGE_ID
        )
        self.assertEqual(package["licenseDeclared"], MODULE.LICENSE_ID)
        self.assertEqual(package["checksums"][0]["checksumValue"], "b" * 64)

    def test_tampered_extracted_text_fails_closed(self) -> None:
        document = MODULE.enrich_document(base_document(), **contract())
        document["hasExtractedLicensingInfos"][0]["extractedText"] = "abbreviated"
        with self.assertRaisesRegex(MODULE.SpdxLicenseError, "absent or stale"):
            MODULE.validate_document(document, **contract())

    def test_wrong_spdx_version_or_artifact_digest_is_rejected(self) -> None:
        document = base_document()
        document["spdxVersion"] = "SPDX-2.2"
        with self.assertRaisesRegex(MODULE.SpdxLicenseError, r"SPDX-2\.3"):
            MODULE.enrich_document(document, **contract())
        invalid = contract()
        invalid["artifact_digest"] = "latest"
        with self.assertRaisesRegex(MODULE.SpdxLicenseError, "artifact digest"):
            MODULE.enrich_document(base_document(), **invalid)


if __name__ == "__main__":
    unittest.main()
