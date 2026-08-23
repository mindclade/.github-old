#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Validate shared evidence schemas and the MCCE1-sealed control policy."""

from __future__ import annotations

import hashlib
import json
import struct
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "evidence"
SCHEMAS = (
    "common.schema.json",
    "deployment-bundle-v1.schema.json",
    "deployment-bundle.schema.json",
    "eligibility-decision.schema.json",
    "evidence-claim.schema.json",
    "evidence-exception.schema.json",
    "evidence-verification.schema.json",
    "production-controls.schema.json",
)
REPOSITORIES = [
    ".github",
    ".github-private",
    "bootstrap",
    "github-config",
    "gitops",
    "infrastructure-live",
    "mindclade-internal-monorepo",
]
DEPLOYMENT_SCHEMA_VERSIONS = {
    "deployment-bundle-v1.schema.json": "mindclade.dev/deployment-bundle/v1",
    "deployment-bundle.schema.json": "mindclade.dev/deployment-bundle/v2",
}
DEPLOYMENT_V1_FIELDS = {
    "schema_version",
    "bundle_digest",
    "change_reference",
    "environment",
    "repositories",
    "release_digests",
    "gitops_render_digest",
    "deployment_selection_digest",
    "infrastructure_handoff_digest",
    "governance_audit_digest",
    "workflow_release",
    "policy_bundle_digest",
}
DEPLOYMENT_V2_FIELDS = DEPLOYMENT_V1_FIELDS | {
    "workflow_release_provenance",
    "module_release",
    "bootstrap_contract",
    "saved_plan_digest",
    "applied_outputs_digest",
    "rollback",
}


def load(name: str) -> dict[str, Any]:
    value = json.loads((CONTRACTS / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain one object")
    return value


def field(key: str, value: bytes) -> bytes:
    encoded_key = key.encode("utf-8")
    return struct.pack(">H", len(encoded_key)) + encoded_key + struct.pack(">I", len(value)) + value


def text(key: str, value: str) -> bytes:
    return field(key, value.encode("utf-8"))


def u64(key: str, value: int) -> bytes:
    return field(key, struct.pack(">Q", value))


def timestamp(key: str, value: str) -> bytes:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    milliseconds = int(parsed.timestamp() * 1000)
    return u64(key, milliseconds)


def string_set(key: str, values: list[str]) -> bytes:
    payload = struct.pack(">I", len(values))
    for value in values:
        encoded = value.encode("utf-8")
        payload += struct.pack(">I", len(encoded)) + encoded
    return field(key, payload)


def go_duration(nanoseconds: int) -> str:
    hour = 3_600_000_000_000
    if nanoseconds <= 0 or nanoseconds % hour:
        raise ValueError("production control maximum_age must be a positive whole hour")
    return f"{nanoseconds // hour}h0m0s"


def validate_deployment_schema(name: str, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_version = DEPLOYMENT_SCHEMA_VERSIONS[name]
    expected_fields = (
        DEPLOYMENT_V1_FIELDS
        if name == "deployment-bundle-v1.schema.json"
        else DEPLOYMENT_V2_FIELDS
    )
    if schema.get("additionalProperties") is not False:
        errors.append(f"{name} must reject unknown top-level fields")
    if set(schema.get("required", [])) != expected_fields:
        errors.append(f"{name} does not require its exact versioned field set")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return errors + [f"{name} properties must be one object"]
    if properties.get("schema_version") != {"const": expected_version}:
        errors.append(f"{name} does not bind {expected_version}")
    try:
        repository_enum = properties["repositories"]["items"]["properties"]["repository"][
            "enum"
        ]
    except (KeyError, TypeError):
        errors.append(f"{name} omits the repository inventory")
    else:
        if repository_enum != REPOSITORIES:
            errors.append(
                f"{name} repository inventory is not the exact seven-repository estate"
            )
    if name == "deployment-bundle.schema.json":
        if properties.get("release_digests", {}).get("uniqueItems") is not True:
            errors.append("deployment-bundle.schema.json must reject duplicate release digests")
        definitions = schema.get("$defs")
        if not isinstance(definitions, dict) or set(definitions) != {
            "commit",
            "releaseProvenance",
            "moduleReleaseProvenance",
        }:
            errors.append(
                "deployment-bundle.schema.json omits exact release provenance definitions"
            )
        else:
            required = set(definitions["moduleReleaseProvenance"].get("required", []))
            if "module_manifest_digest" not in required:
                errors.append(
                    "deployment-bundle.schema.json does not require module manifest provenance"
                )
    return errors


def policy_digest(policy: dict[str, Any]) -> str:
    controls = [
        f"{control['id']}|{control['owner']}|{go_duration(control['maximum_age'])}|"
        f"{'true' if control['exception_allowed'] else 'false'}"
        for control in policy["controls"]
    ]
    payload = b"MCCE1/production-control-policy/v1\x00"
    payload += text("id", policy["id"])
    payload += text("version", policy["version"])
    payload += u64("epoch", policy["epoch"])
    payload += timestamp("valid_until", policy["valid_until"])
    payload += string_set("controls", controls)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    for name in SCHEMAS:
        try:
            schema = load(name)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{name} is not a Draft 2020-12 schema")
        if not str(schema.get("$id", "")).startswith("https://mindclade.dev/contracts/evidence/"):
            errors.append(f"{name} has a noncanonical identifier")

    try:
        policy = load("production-controls.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return sorted(set(errors + [str(exc)]))
    expected_keys = {"id", "version", "digest", "epoch", "valid_until", "controls"}
    if set(policy) != expected_keys:
        errors.append("production-controls.json has unexpected fields")
    controls = policy.get("controls", [])
    control_ids = [str(control.get("id", "")) for control in controls if isinstance(control, dict)]
    if control_ids != sorted(set(control_ids)) or not control_ids:
        errors.append("production controls must be sorted, unique, and nonempty")
    for control in controls:
        if not isinstance(control, dict) or set(control) != {"id", "owner", "maximum_age", "exception_allowed"}:
            errors.append("production control entries must use the exact contract")
            continue
        if not isinstance(control["maximum_age"], int) or control["maximum_age"] <= 0:
            errors.append(f"production control {control['id']} has invalid maximum_age")
    try:
        actual_digest = policy_digest(policy)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"production policy cannot be sealed: {exc}")
    else:
        if policy.get("digest") != actual_digest:
            errors.append(f"production policy digest mismatch: {policy.get('digest')} != {actual_digest}")

    for name in DEPLOYMENT_SCHEMA_VERSIONS:
        try:
            errors.extend(validate_deployment_schema(name, load(name)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    return sorted(set(errors))


def main() -> int:
    errors = validate()
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("evidence contracts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
