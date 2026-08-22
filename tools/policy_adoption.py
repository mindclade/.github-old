#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Create a consumer record binding a policy bundle to its immutable v5 release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[1-9][0-9]*$")
EXPECTED_KEYS = {
    "schemaVersion",
    "bundleId",
    "bundleVersion",
    "releaseTag",
    "releaseCommit",
    "manifestSha256",
    "validatorSha256",
}


class AdoptionError(ValueError):
    pass


def digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise AdoptionError(f"cannot read {path}: {exc}") from exc


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdoptionError(f"{label} must be one JSON object")
    return value


def create_record(
    manifest_path: Path,
    validator_path: Path,
    release_tag: str,
    release_commit: str,
) -> dict[str, Any]:
    manifest = load_object(manifest_path, "policy manifest")
    if manifest.get("bundleId") != "mindclade-policy-bundle":
        raise AdoptionError("policy manifest bundleId is not canonical")
    version = manifest.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise AdoptionError("policy manifest version is malformed")
    if release_tag != "v5.0.0":
        raise AdoptionError("policy adoption is limited to published v5.0.0")
    if not SHA.fullmatch(release_commit):
        raise AdoptionError("release commit must be one lowercase 40-character SHA")
    return {
        "bundleId": "mindclade-policy-bundle",
        "bundleVersion": version,
        "manifestSha256": digest(manifest_path),
        "releaseCommit": release_commit,
        "releaseTag": release_tag,
        "schemaVersion": 1,
        "validatorSha256": digest(validator_path),
    }


def validate_record(value: dict[str, Any]) -> None:
    if set(value) != EXPECTED_KEYS:
        raise AdoptionError(f"adoption record keys must be exactly {sorted(EXPECTED_KEYS)}")
    if value.get("schemaVersion") != 1 or value.get("bundleId") != "mindclade-policy-bundle":
        raise AdoptionError("adoption record identity is invalid")
    if not isinstance(value.get("bundleVersion"), str) or not VERSION.fullmatch(
        value["bundleVersion"]
    ):
        raise AdoptionError("adoption record bundleVersion is malformed")
    if value.get("releaseTag") != "v5.0.0" or not SHA.fullmatch(
        str(value.get("releaseCommit", ""))
    ):
        raise AdoptionError("adoption record release identity is invalid")
    for field in ("manifestSha256", "validatorSha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(value.get(field, ""))):
            raise AdoptionError(f"adoption record {field} is malformed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--release-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        record = create_record(
            args.manifest, args.validator, args.release_tag, args.release_commit
        )
        validate_record(record)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (AdoptionError, OSError) as exc:
        print(f"policy adoption rejected: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
