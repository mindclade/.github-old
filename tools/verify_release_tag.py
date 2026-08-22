#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Verify a signed annotated release tag through GitHub's read-only Git Data API."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any


GITHUB_API_HOST = "github.com"
GITHUB_API_VERSION = "2026-03-10"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")


class TagVerificationError(ValueError):
    """Raised when the requested tag is not an exact verified release identity."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TagVerificationError(f"{label} is not an object")
    return value


def _validate_identity(repository: str, tag: str, expected_source: str) -> None:
    if not REPOSITORY.fullmatch(repository):
        raise TagVerificationError("repository must be one owner/name slug")
    if not TAG.fullmatch(tag):
        raise TagVerificationError("release tag must be canonical full SemVer vX.Y.Z")
    if not SHA.fullmatch(expected_source):
        raise TagVerificationError(
            "expected source must be one lowercase 40-character SHA"
        )


def verify(
    repository: str,
    tag: str,
    expected_source: str,
    reference: dict[str, Any],
    tag_object: dict[str, Any],
) -> None:
    """Verify one Git reference and annotated-tag response without network access."""

    _validate_identity(repository, tag, expected_source)

    ref_object = _mapping(reference.get("object"), "tag reference object")
    tag_object_sha = ref_object.get("sha")
    if reference.get("ref") != f"refs/tags/{tag}":
        raise TagVerificationError(
            "Git reference name does not match the requested release tag"
        )
    if ref_object.get("type") != "tag" or not isinstance(tag_object_sha, str):
        raise TagVerificationError("release identity is not an annotated tag object")
    if not SHA.fullmatch(tag_object_sha):
        raise TagVerificationError("annotated tag object SHA is malformed")

    target = _mapping(tag_object.get("object"), "annotated tag target")
    verification = _mapping(tag_object.get("verification"), "tag verification")
    tagger = _mapping(tag_object.get("tagger"), "annotated tagger")
    if tag_object.get("sha") != tag_object_sha or tag_object.get("tag") != tag:
        raise TagVerificationError(
            "annotated tag object does not match its Git reference"
        )
    if not isinstance(tag_object.get("message"), str) or not tag_object["message"].strip():
        raise TagVerificationError("annotated tag omits its release message")
    if target.get("type") != "commit" or target.get("sha") != expected_source:
        raise TagVerificationError(
            "annotated tag does not target the expected source commit"
        )
    if verification.get("verified") is not True or verification.get("reason") != "valid":
        raise TagVerificationError(
            "annotated tag signature is not GitHub-verified and valid"
        )
    for field in ("signature", "payload", "verified_at"):
        if not isinstance(verification.get(field), str) or not verification[field].strip():
            raise TagVerificationError(f"tag verification omits {field}")
    for field in ("name", "email", "date"):
        if not isinstance(tagger.get(field), str) or not tagger[field].strip():
            raise TagVerificationError(f"annotated tagger omits {field}")


def _gh_get(path: str) -> dict[str, Any]:
    if not path.startswith("/repos/"):
        raise TagVerificationError("refusing a non-repository GitHub API path")
    try:
        result = subprocess.run(
            [
                "gh",
                "api",
                "--hostname",
                GITHUB_API_HOST,
                "--method",
                "GET",
                "--header",
                "Accept: application/vnd.github+json",
                "--header",
                f"X-GitHub-Api-Version: {GITHUB_API_VERSION}",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as error:
        raise TagVerificationError("gh is not installed") from error
    except subprocess.TimeoutExpired as error:
        raise TagVerificationError(f"GitHub GET timed out: {path}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or f"exit status {error.returncode}"
        raise TagVerificationError(f"GitHub GET failed for {path}: {detail}") from error
    try:
        return _mapping(json.loads(result.stdout), f"GitHub response for {path}")
    except json.JSONDecodeError as error:
        raise TagVerificationError(f"GitHub returned invalid JSON for {path}") from error


def verify_connected(repository: str, tag: str, expected_source: str) -> None:
    """Read and verify one release tag from the GitHub API."""

    _validate_identity(repository, tag, expected_source)
    reference = _gh_get(f"/repos/{repository}/git/ref/tags/{tag}")
    ref_object = _mapping(reference.get("object"), "tag reference object")
    tag_object_sha = ref_object.get("sha")
    if not isinstance(tag_object_sha, str) or not SHA.fullmatch(tag_object_sha):
        raise TagVerificationError(
            "tag reference does not resolve to a valid object SHA"
        )
    tag_object = _gh_get(f"/repos/{repository}/git/tags/{tag_object_sha}")
    verify(repository, tag, expected_source, reference, tag_object)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--expected-source", required=True)
    args = parser.parse_args()
    try:
        verify_connected(args.repository, args.tag, args.expected_source)
    except TagVerificationError as error:
        print(f"release tag rejected: {error}", file=sys.stderr)
        return 1
    print(f"verified signed annotated release tag {args.tag} at {args.expected_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
