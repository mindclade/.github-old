#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
release_tag = importlib.import_module("tools.verify_release_tag")
SOURCE = "a" * 40
TAG_OBJECT = "b" * 40


def signed_tag() -> tuple[dict[str, object], dict[str, object]]:
    reference: dict[str, object] = {
        "ref": "refs/tags/v5.0.0",
        "object": {"type": "tag", "sha": TAG_OBJECT},
    }
    tag_object: dict[str, object] = {
        "sha": TAG_OBJECT,
        "tag": "v5.0.0",
        "message": "Mindclade shared workflow contract v5",
        "object": {"type": "commit", "sha": SOURCE},
        "tagger": {
            "name": "Mindclade Release",
            "email": "release@mindclade.com",
            "date": "2026-08-22T00:00:00Z",
        },
        "verification": {
            "verified": True,
            "reason": "valid",
            "signature": "-----BEGIN SSH SIGNATURE-----",
            "payload": f"object {SOURCE}",
            "verified_at": "2026-08-22T00:00:01Z",
        },
    }
    return reference, tag_object


class ReleaseTagTests(unittest.TestCase):
    def test_verified_annotated_tag_is_accepted(self) -> None:
        reference, tag_object = signed_tag()
        release_tag.verify("mindclade/.github", "v5.0.0", SOURCE, reference, tag_object)

    def test_unsigned_tag_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        tag_object["verification"] = {
            "verified": False,
            "reason": "unsigned",
            "signature": None,
            "payload": None,
            "verified_at": None,
        }
        with self.assertRaisesRegex(release_tag.TagVerificationError, "not GitHub-verified"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", SOURCE, reference, tag_object
            )

    def test_lightweight_tag_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        reference["object"] = {"type": "commit", "sha": SOURCE}
        with self.assertRaisesRegex(release_tag.TagVerificationError, "not an annotated tag"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", SOURCE, reference, tag_object
            )

    def test_wrong_target_commit_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        with self.assertRaisesRegex(release_tag.TagVerificationError, "expected source"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", "c" * 40, reference, tag_object
            )

    def test_mismatched_reference_name_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        reference["ref"] = "refs/tags/v5.0.1"
        with self.assertRaisesRegex(release_tag.TagVerificationError, "reference name"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", SOURCE, reference, tag_object
            )

    def test_mismatched_tag_object_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        tag_object["sha"] = "c" * 40
        with self.assertRaisesRegex(release_tag.TagVerificationError, "does not match"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", SOURCE, reference, tag_object
            )

    def test_missing_release_message_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        tag_object["message"] = ""
        with self.assertRaisesRegex(release_tag.TagVerificationError, "release message"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", SOURCE, reference, tag_object
            )

    def test_incomplete_github_verification_is_rejected(self) -> None:
        reference, tag_object = signed_tag()
        verification = tag_object["verification"]
        assert isinstance(verification, dict)
        verification["verified_at"] = None
        with self.assertRaisesRegex(release_tag.TagVerificationError, "verified_at"):
            release_tag.verify(
                "mindclade/.github", "v5.0.0", SOURCE, reference, tag_object
            )

    def test_malformed_identity_fails_before_connected_lookup(self) -> None:
        with mock.patch.object(release_tag, "_gh_get") as get:
            with self.assertRaisesRegex(release_tag.TagVerificationError, "lowercase"):
                release_tag.verify_connected(
                    "mindclade/.github", "v5.0.0", SOURCE.upper()
                )
        get.assert_not_called()

    def test_connected_lookup_pins_host_version_and_tag_object_sha(self) -> None:
        reference, tag_object = signed_tag()
        responses = [
            subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(reference), stderr=""
            ),
            subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(tag_object), stderr=""
            ),
        ]
        with mock.patch.object(
            release_tag.subprocess, "run", side_effect=responses
        ) as run:
            release_tag.verify_connected("mindclade/.github", "v5.0.0", SOURCE)
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                [
                    "gh",
                    "api",
                    "--hostname",
                    "github.com",
                    "--method",
                    "GET",
                    "--header",
                    "Accept: application/vnd.github+json",
                    "--header",
                    "X-GitHub-Api-Version: 2026-03-10",
                    "/repos/mindclade/.github/git/ref/tags/v5.0.0",
                ],
                [
                    "gh",
                    "api",
                    "--hostname",
                    "github.com",
                    "--method",
                    "GET",
                    "--header",
                    "Accept: application/vnd.github+json",
                    "--header",
                    "X-GitHub-Api-Version: 2026-03-10",
                    f"/repos/mindclade/.github/git/tags/{TAG_OBJECT}",
                ],
            ],
        )
        for call in run.call_args_list:
            self.assertEqual(
                call.kwargs,
                {
                    "check": True,
                    "capture_output": True,
                    "text": True,
                    "timeout": 30,
                },
            )

    def test_invalid_github_response_is_rejected(self) -> None:
        result = subprocess.CompletedProcess([], 0, stdout="not-json", stderr="")
        with mock.patch.object(release_tag.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(release_tag.TagVerificationError, "invalid JSON"):
                release_tag.verify_connected(
                    "mindclade/.github", "v5.0.0", SOURCE
                )

    def test_subtree_release_tags_fail_closed_without_a_signer(self) -> None:
        text = (
            ROOT / ".github" / "workflows" / "reusable-subtree-mirror.yml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("git tag -f", text)
        self.assertNotIn("git mktag", text)
        self.assertNotIn('refs/tags/${TAG}', text)
        self.assertIn("subtree target tag creation is blocked", text)
        self.assertIn("GitHub-verified signing authority", text)
        self.assertIn('[[ "/$SUBTREE_PATH/" = *"/./"* ]]', text)
        self.assertIn('[[ "/$SUBTREE_PATH/" = *"//"* ]]', text)
        self.assertIn('git ls-files -- "$SUBTREE_PATH"', text)


if __name__ == "__main__":
    unittest.main()
