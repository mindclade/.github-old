#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Validate a workflow-release specification and exact-tag source attestation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CONTRACTS = ROOT / "contracts" / "workflows"
SHA = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
WORKFLOW = re.compile(r"^reusable-[a-z0-9-]+\.yml$")


class SpecError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SpecError(f"{path} must contain one JSON object")
    return value


def exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise SpecError(f"{label} keys must be exactly {sorted(expected)}")


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_spec(path: Path) -> dict[str, Any]:
    value = load(path)
    exact_keys(
        value,
        {
            "schema_version",
            "release_tag",
            "contract_major",
            "change_class",
            "required_workflows",
            "qualification",
            "publication",
        },
        "release specification",
    )
    if value["schema_version"] != 1 or value["contract_major"] != 5:
        raise SpecError("release specification must declare schema 1 and contract major 5")
    if value["change_class"] != "major" or not TAG.fullmatch(str(value["release_tag"])):
        raise SpecError("release specification must declare one full-semver major release")
    if path.name != f"{value['release_tag']}.json":
        raise SpecError("release specification filename must match release_tag")

    workflows = value["required_workflows"]
    if (
        not isinstance(workflows, list)
        or not workflows
        or workflows != sorted(workflows)
        or len(workflows) != len(set(workflows))
        or not all(isinstance(item, str) and WORKFLOW.fullmatch(item) for item in workflows)
    ):
        raise SpecError("required_workflows must be a sorted unique list of reusable workflows")
    for workflow in workflows:
        workflow_path = WORKFLOWS / workflow
        contract_path = CONTRACTS / workflow.replace(".yml", ".json")
        if not workflow_path.is_file() or not contract_path.is_file():
            raise SpecError(f"workflow or contract snapshot is absent: {workflow}")

    qualification = value["qualification"]
    if not isinstance(qualification, dict):
        raise SpecError("qualification must be an object")
    exact_keys(
        qualification,
        {"connected_exact_tag", "independent_linux_rebuilds", "native_systems"},
        "qualification",
    )
    if qualification != {
        "connected_exact_tag": True,
        "independent_linux_rebuilds": 2,
        "native_systems": ["aarch64-darwin", "aarch64-linux", "x86_64-linux"],
    }:
        raise SpecError("v5 qualification must require all native systems and two Linux rebuilds")

    publication = value["publication"]
    if not isinstance(publication, dict):
        raise SpecError("publication must be an object")
    exact_keys(
        publication,
        {"draft_on_tag", "protected_environments", "required_approvals"},
        "publication",
    )
    if publication != {
        "draft_on_tag": True,
        "protected_environments": [
            "workflow-release-platform",
            "workflow-release-security",
        ],
        "required_approvals": 2,
    }:
        raise SpecError("publication must remain draft-first with two protected approvals")
    return value


def attest(spec_path: Path, source: str, output: Path) -> None:
    if not SHA.fullmatch(source):
        raise SpecError("source commit must be one lowercase 40-character SHA")
    spec = validate_spec(spec_path)
    files: dict[str, str] = {}
    for workflow in spec["required_workflows"]:
        workflow_path = WORKFLOWS / workflow
        contract_path = CONTRACTS / workflow.replace(".yml", ".json")
        files[workflow_path.relative_to(ROOT).as_posix()] = sha256(workflow_path)
        files[contract_path.relative_to(ROOT).as_posix()] = sha256(contract_path)
    result = {
        "schema_version": 1,
        "release_tag": spec["release_tag"],
        "source_commit": source,
        "release_spec_digest": sha256(spec_path),
        "files": dict(sorted(files.items())),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(spec_path: Path, attestation_path: Path, expected_source: str) -> None:
    if not SHA.fullmatch(expected_source):
        raise SpecError("expected source commit is malformed")
    attestation = load(attestation_path)
    exact_keys(
        attestation,
        {"schema_version", "release_tag", "source_commit", "release_spec_digest", "files"},
        "source attestation",
    )
    spec = validate_spec(spec_path)
    if attestation["schema_version"] != 1:
        raise SpecError("unsupported source attestation schema")
    if attestation["release_tag"] != spec["release_tag"]:
        raise SpecError("source attestation release tag does not match")
    if attestation["source_commit"] != expected_source:
        raise SpecError("source attestation commit does not match the annotated tag")
    if attestation["release_spec_digest"] != sha256(spec_path):
        raise SpecError("release specification digest does not match")
    files = attestation["files"]
    expected_files = {
        path
        for workflow in spec["required_workflows"]
        for path in (
            f".github/workflows/{workflow}",
            f"contracts/workflows/{workflow.removesuffix('.yml')}.json",
        )
    }
    if not isinstance(files, dict) or set(files) != expected_files:
        raise SpecError("source attestation file inventory is not exact")
    for relative, expected_digest in files.items():
        path = (ROOT / str(relative)).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise SpecError("source attestation file escapes the repository") from exc
        if not path.is_file() or sha256(path) != expected_digest:
            raise SpecError(f"source attestation digest mismatch: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--attest-source")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-attestation", type=Path)
    parser.add_argument("--expected-source")
    args = parser.parse_args()
    try:
        if args.attest_source or args.output:
            if not args.attest_source or args.output is None:
                raise SpecError("--attest-source and --output are required together")
            attest(args.spec, args.attest_source, args.output)
        elif args.verify_attestation or args.expected_source:
            if args.verify_attestation is None or not args.expected_source:
                raise SpecError("--verify-attestation and --expected-source are required together")
            verify(args.spec, args.verify_attestation, args.expected_source)
        else:
            validate_spec(args.spec)
    except SpecError as exc:
        print(f"release specification rejected: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
