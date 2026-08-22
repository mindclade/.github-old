#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Validate immutable source evidence for a shared-workflow release.

This validator deliberately does not query GitHub or create a tag. A missing local tag is a
connected qualification precondition, not evidence that a remote tag is absent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "contracts" / "releases" / "v4.0.0.json"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def git(root: Path, *arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return result.stdout.strip() if result.returncode == 0 else ""


def resolve_mainline(root: Path, preferred: str = "") -> str:
    """The ref the release lineage must descend from, or "" if none is present.

    A remote-tracking main is preferred over a local one: it is what a fresh clone and a
    `fetch-depth: 0` checkout both have, and it cannot be moved by local work.
    """
    candidates = (preferred,) if preferred else ("refs/remotes/origin/main", "refs/heads/main")
    for ref in candidates:
        if ref and git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False):
            return ref
    return ""


def lineage_status(root: Path, commit: str, mainline: str) -> str:
    """Whether `commit` is still reachable from `mainline`.

    Object existence is not reachability. A squash or rebase merge leaves the attested commit
    in the object database — held alive by a stale local branch, a preserved rescue tag, or a
    PR head ref — while main no longer descends from it. Checking only `cat-file -e` therefore
    passes in the workspace that did the merge and fails in every fresh clone, which is the one
    place the release contract has to hold.
    """
    if not mainline:
        return "unverified"
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", commit, mainline],
        check=False,
        capture_output=True,
    )
    return "ancestor" if result.returncode == 0 else "diverged"


def validate_manifest(
    manifest: dict[str, Any],
    root: Path,
    require_local_tag: bool = False,
    mainline_ref: str = "",
) -> tuple[list[str], str]:
    errors: list[str] = []
    release = manifest.get("release")
    commit = str(manifest.get("source_commit", ""))
    source_tree = str(manifest.get("source_tree", ""))
    required_tag = manifest.get("required_tag", {})

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if release != "v4.0.0":
        errors.append("release manifest must describe v4.0.0")
    if manifest.get("qualification") != (
        "source-qualified; connected tag and release evidence required"
    ):
        errors.append("qualification must preserve the connected-evidence boundary")
    if not SHA1_RE.fullmatch(commit):
        errors.append("source_commit must be a full 40-character Git object id")
    if not SHA1_RE.fullmatch(source_tree):
        errors.append("source_tree must be a full 40-character Git tree id")
    if required_tag != {
        "name": "v4.0.0",
        "object_type": "tag",
        "target_commit": commit,
        "operator_created": True,
        "move_or_reuse_forbidden": True,
    }:
        errors.append("required_tag must require an operator-created immutable annotated tag")
    connected = manifest.get("connected_evidence", {})
    if connected.get("required") is not True or len(connected.get("claims", [])) < 5:
        errors.append("connected evidence must remain required and enumerate every release gate")

    if errors or not SHA1_RE.fullmatch(commit):
        return errors, "unknown"

    try:
        git(root, "cat-file", "-e", f"{commit}^{{commit}}")

        mainline = resolve_mainline(root, mainline_ref)
        if lineage_status(root, commit, mainline) == "diverged":
            errors.append(
                f"source_commit {commit} is not an ancestor of {mainline}; the release "
                "lineage was rewritten by a squash or rebase merge and cannot be "
                "reproduced from a fresh clone"
            )

        actual_tree = git(root, "rev-parse", f"{commit}^{{tree}}")
        if actual_tree != source_tree:
            errors.append(
                f"source tree mismatch: manifest={source_tree}, git={actual_tree}"
            )

        surfaces = manifest.get("release_surfaces", {})
        if not isinstance(surfaces, dict) or not surfaces:
            errors.append("release_surfaces must be a non-empty object")
        else:
            for path, expected in sorted(surfaces.items()):
                if not SHA1_RE.fullmatch(str(expected)):
                    errors.append(f"release surface {path} has an invalid tree id")
                    continue
                actual = git(root, "rev-parse", f"{commit}:{path}")
                if actual != expected:
                    errors.append(
                        f"release surface {path} mismatch: manifest={expected}, git={actual}"
                    )

        required_files = manifest.get("required_files", {})
        if not isinstance(required_files, dict) or not required_files:
            errors.append("required_files must be a non-empty object")
        else:
            for path, expected in sorted(required_files.items()):
                if not SHA256_RE.fullmatch(str(expected)):
                    errors.append(f"required file {path} has an invalid SHA-256 digest")
                    continue
                data = subprocess.run(
                    ["git", "-C", str(root), "show", f"{commit}:{path}"],
                    check=False,
                    capture_output=True,
                )
                if data.returncode != 0:
                    errors.append(f"required file is absent at source_commit: {path}")
                    continue
                actual = "sha256:" + hashlib.sha256(data.stdout).hexdigest()
                if actual != expected:
                    errors.append(
                        f"required file {path} mismatch: manifest={expected}, git={actual}"
                    )

        changelog = git(root, "show", f"{commit}:CHANGELOG.md")
        if not re.search(r"(?m)^## v4\.0\.0(?:\s|$)", changelog):
            errors.append("source commit has no v4.0.0 changelog section")
    except ValueError as error:
        errors.append(f"cannot resolve release source evidence: {error}")

    tag_ref = "refs/tags/v4.0.0"
    tag_object = git(root, "rev-parse", "--verify", tag_ref, check=False)
    tag_status = "absent"
    if tag_object:
        tag_status = "present"
        object_type = git(root, "cat-file", "-t", tag_ref)
        if object_type != "tag":
            errors.append("local v4.0.0 is not an annotated tag object")
        resolved = git(root, "rev-parse", f"{tag_ref}^{{commit}}")
        if resolved != commit:
            errors.append(
                f"local v4.0.0 resolves to {resolved}, expected source_commit {commit}"
            )
    elif require_local_tag:
        errors.append(
            "local v4.0.0 tag is absent; fetch authoritative refs before release qualification"
        )

    return errors, tag_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-local-tag", action="store_true")
    parser.add_argument(
        "--mainline-ref",
        default="",
        help="ref the release commit must descend from (default: origin/main, then main)",
    )
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"release readiness failed: cannot read manifest: {error}", file=sys.stderr)
        return 1

    root = args.root.resolve()
    errors, tag_status = validate_manifest(
        manifest,
        root,
        require_local_tag=args.require_local_tag,
        mainline_ref=args.mainline_ref,
    )
    mainline = resolve_mainline(root, args.mainline_ref)
    lineage = lineage_status(root, str(manifest.get("source_commit", "")), mainline)
    if errors:
        print("release readiness failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        "v4.0.0 source evidence passed; "
        f"lineage={lineage}{f' ({mainline})' if mainline else ''}; "
        f"local tag={tag_status}; connected tag/release qualification remains required"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

