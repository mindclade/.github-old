#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Verify a consumer's v5 policy adoption record against local and action bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


EXPECTED_KEYS = {
    "schemaVersion",
    "bundleId",
    "bundleVersion",
    "releaseTag",
    "releaseCommit",
    "manifestSha256",
    "validatorSha256",
}
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[1-9][0-9]*$")


class AdoptionError(ValueError):
    pass


def digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise AdoptionError(f"cannot read {path}: {exc}") from exc


def confined(root: Path, raw: str, label: str) -> Path:
    path = Path(raw)
    if not raw or path.is_absolute() or "\\" in raw or ".." in path.parts:
        raise AdoptionError(f"{label} must be a workspace-relative path")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise AdoptionError(f"{label} escapes the workspace") from exc
    return resolved


def load_record(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"cannot read adoption record {path}: {exc}") from exc
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        raise AdoptionError(f"adoption record keys must be exactly {sorted(EXPECTED_KEYS)}")
    if value["schemaVersion"] != 1 or value["bundleId"] != "mindclade-policy-bundle":
        raise AdoptionError("adoption record identity is invalid")
    if not isinstance(value["bundleVersion"], str) or not VERSION.fullmatch(
        value["bundleVersion"]
    ):
        raise AdoptionError("adoption record bundleVersion is malformed")
    if value["releaseTag"] != "v5.0.0" or not SHA.fullmatch(value["releaseCommit"]):
        raise AdoptionError("adoption record release identity is invalid")
    if not DIGEST.fullmatch(value["manifestSha256"]) or not DIGEST.fullmatch(
        value["validatorSha256"]
    ):
        raise AdoptionError("adoption record digest is malformed")
    return value


def verify(
    workspace: Path,
    action_root: Path,
    action_ref: str,
    adoption_record: str,
    local_validator: str,
) -> None:
    record = load_record(confined(workspace, adoption_record, "adoption record path"))
    if action_ref != record["releaseCommit"]:
        raise AdoptionError("action ref does not match the adopted release commit")
    manifest = confined(
        workspace, "contracts/policy-bundle/manifest.json", "policy manifest path"
    )
    try:
        manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"cannot read consumer policy manifest: {exc}") from exc
    if manifest_value.get("bundleId") != record["bundleId"] or manifest_value.get(
        "version"
    ) != record["bundleVersion"]:
        raise AdoptionError("consumer policy manifest identity differs from adoption record")
    if digest(manifest) != record["manifestSha256"]:
        raise AdoptionError("consumer policy manifest digest differs from adoption record")
    released_validator = action_root / "validate.py"
    if digest(released_validator) != record["validatorSha256"]:
        raise AdoptionError("released validator digest differs from adoption record")
    if local_validator:
        mirror = confined(workspace, local_validator, "local validator path")
        if digest(mirror) != record["validatorSha256"]:
            raise AdoptionError("local validator digest differs from adoption record")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--action-root", type=Path, required=True)
    parser.add_argument("--action-ref", required=True)
    parser.add_argument("--adoption-record", required=True)
    parser.add_argument("--local-validator", default="")
    args = parser.parse_args()
    try:
        verify(
            args.workspace,
            args.action_root,
            args.action_ref,
            args.adoption_record,
            args.local_validator,
        )
    except AdoptionError as exc:
        print(f"policy adoption rejected: {exc}", file=sys.stderr)
        return 1
    print("policy adoption provenance verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
