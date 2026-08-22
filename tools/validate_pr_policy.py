#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Validate non-draft pull-request authorization and policy-release metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


AUTHORIZATION_PHRASES = (
    "I am authorized under a current written agreement with Mindclade, LLC.",
    "I identified every third-party component, dataset, model, font, media,",
    "I updated `LICENSE`, `NOTICE`, the SBOM, or other license evidence",
)
HOLD_MARKER = re.compile(r"\bDO\s+NOT\s+MERGE\b", re.IGNORECASE)
UNPUBLISHED_MARKERS = (
    re.compile(r"\bsource[- ]candidate\b", re.IGNORECASE),
    re.compile(r"\bcandidate\s*;\s*not\s+published\b", re.IGNORECASE),
    re.compile(r"\bunpublished[- ]release\b", re.IGNORECASE),
)
POLICY_MARKER = re.compile(
    r"<!--\s*mindclade-policy-bundle:\s*"
    r"version=(?P<version>[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[1-9][0-9]*);\s*"
    r"release=(?P<release>v[0-9]+\.[0-9]+\.[0-9]+);\s*"
    r"release_commit=(?P<commit>[0-9a-f]{40});\s*"
    r"status=(?P<status>[a-z-]+)\s*-->",
    re.IGNORECASE,
)
REPOSITORY = re.compile(r"^mindclade/[A-Za-z0-9_.-]+$")


class PolicyError(ValueError):
    pass


def load_event(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot read pull-request event: {exc}") from exc
    if not isinstance(value, dict):
        raise PolicyError("pull-request event must be one JSON object")
    return value


def load_changed_files(path: Path) -> list[str]:
    try:
        values = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PolicyError(f"cannot read changed-file inventory: {exc}") from exc
    files: list[str] = []
    for raw in values:
        value = raw.strip()
        candidate = Path(value)
        if (
            not value
            or candidate.is_absolute()
            or "\\" in value
            or any(part in {"", ".", ".."} for part in candidate.parts)
        ):
            raise PolicyError(f"changed-file path is not normalized: {raw!r}")
        files.append(candidate.as_posix())
    return files


def provenance_paths(manifest_path: Path, repository: str) -> set[str]:
    if not REPOSITORY.fullmatch(repository):
        raise PolicyError("repository must be a canonical mindclade owner/name slug")
    if repository == "mindclade/.github":
        # The canonical source is reviewed before its immutable release exists. Requiring
        # published-release provenance here would deadlock the release bootstrap.
        return set()
    repository_name = repository.split("/", 1)[1]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot read policy manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("bundleId") != "mindclade-policy-bundle":
        raise PolicyError("policy manifest identity is invalid")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise PolicyError("policy manifest artifacts must be a list")
    paths = {
        "contracts/policy-bundle/adoption.json",
        "contracts/policy-bundle/manifest.json",
    }
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise PolicyError("policy manifest artifact must be an object")
        distributions = artifact.get("distributions")
        if not isinstance(distributions, list):
            raise PolicyError("policy manifest distributions must be a list")
        for distribution in distributions:
            if not isinstance(distribution, dict):
                raise PolicyError("policy manifest distribution must be an object")
            if distribution.get("repository") == repository_name:
                target = distribution.get("path")
                if not isinstance(target, str) or not target:
                    raise PolicyError("policy manifest distribution path is invalid")
                paths.add(target)
    return paths


def requires_provenance(
    manifest_path: Path, repository: str, changed_files: list[str]
) -> bool:
    governed = provenance_paths(manifest_path, repository)
    return bool(governed.intersection(changed_files))


def validate_body(
    event: dict[str, Any],
    expected_bundle_version: str,
    expected_release_tag: str,
    expected_release_commit: str,
    provenance_required: bool = False,
) -> list[str]:
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        return []
    if pull_request.get("draft") is True:
        return []
    title = str(pull_request.get("title") or "")
    body = str(pull_request.get("body") or "")
    combined = f"{title}\n{body}"
    errors: list[str] = []
    if HOLD_MARKER.search(combined):
        errors.append("non-draft pull request contains a DO NOT MERGE hold marker")
    for marker in UNPUBLISHED_MARKERS:
        if marker.search(combined):
            errors.append("non-draft pull request refers to an unpublished release candidate")
            break
    for phrase in AUTHORIZATION_PHRASES:
        # The canonical pull-request template wraps long checklist items. Match the
        # prescribed wording while treating Markdown line wrapping as ordinary whitespace.
        phrase_pattern = r"\s+".join(re.escape(part) for part in phrase.split())
        checked = re.search(
            rf"(?mi)^\s*-\s*\[[xX]\]\s*{phrase_pattern}",
            body,
        )
        if not checked:
            errors.append(f"contributor authorization remains unchecked: {phrase}")

    markers = list(POLICY_MARKER.finditer(body))
    if provenance_required and len(markers) != 1:
        errors.append("governed policy changes require exactly one provenance marker")
    elif "mindclade-policy-bundle:" in body.lower() and len(markers) != 1:
        errors.append("policy-bundle provenance marker is malformed or duplicated")
    elif len(markers) == 1:
        marker = markers[0]
        if marker.group("version") != expected_bundle_version:
            errors.append(
                "policy-bundle provenance uses stale version "
                f"{marker.group('version')}; expected {expected_bundle_version}"
            )
        if marker.group("release") != expected_release_tag:
            errors.append(
                "policy-bundle provenance uses unexpected release "
                f"{marker.group('release')}; expected {expected_release_tag}"
            )
        if marker.group("commit").lower() != expected_release_commit:
            errors.append(
                "policy-bundle provenance uses unexpected release commit "
                f"{marker.group('commit')}; expected {expected_release_commit}"
            )
        if marker.group("status").lower() != "published":
            errors.append("policy-bundle provenance must declare status=published")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--changed-files", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--expected-bundle-version", required=True)
    parser.add_argument("--expected-release-tag", required=True)
    parser.add_argument("--expected-release-commit", required=True)
    args = parser.parse_args()
    try:
        event = load_event(args.event)
        if not re.fullmatch(r"[0-9a-f]{40}", args.expected_release_commit):
            raise PolicyError("expected release commit must be one lowercase full SHA")
        changed_files = load_changed_files(args.changed_files)
        provenance_required = requires_provenance(
            args.manifest, args.repository, changed_files
        )
        errors = validate_body(
            event,
            args.expected_bundle_version,
            args.expected_release_tag,
            args.expected_release_commit,
            provenance_required,
        )
    except PolicyError as exc:
        print(f"pull-request policy rejected: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"::error::{error}")
        return 1
    print("pull-request policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
