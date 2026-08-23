#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Validate the v5 workflow release and attest every declared tracked surface."""

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
WORKFLOWS = ROOT / ".github" / "workflows"
CONTRACTS = ROOT / "contracts" / "workflows"
SHA = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
SURFACE_KEYS = {
    "reusable_workflows",
    "workflow_contracts",
    "required_workflows",
    "repository_home_action",
    "release_tools",
    "policy_tools",
    "policy_manifest",
}
REQUIRED_WORKFLOWS = [
    ".github/workflows/required-repository-policy.yml",
    ".github/workflows/required-security-baseline.yml",
]
REPOSITORY_HOME_ACTION = ["actions/validate-repository-home"]
RELEASE_TOOLS = [
    "tools/validate-release-spec.py",
    "tools/verify_release_governance.py",
    "tools/verify_release_tag.py",
]
POLICY_TOOLS = [
    "tools/enrich_spdx_license.py",
    "tools/policy_adoption.py",
    "tools/policy_bundle.py",
    "tools/third_party_notices.py",
    "tools/validate_pr_policy.py",
]
POLICY_MANIFEST = ["contracts/policy-bundle"]


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


def _safe_relative(raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise SpecError(f"{label} must be a nonempty POSIX relative path")
    path = Path(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SpecError(f"{label} must be a normalized relative path")
    return path


def _git_tracked(relative: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", relative.as_posix()],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise SpecError(f"cannot enumerate tracked release surface: {relative}")
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]


def expand_surfaces(spec: dict[str, Any]) -> list[str]:
    surfaces = spec["release_surfaces"]
    files: set[str] = set()
    for category in sorted(SURFACE_KEYS):
        for index, raw in enumerate(surfaces[category]):
            relative = _safe_relative(raw, f"release_surfaces.{category}[{index}]")
            target = ROOT / relative
            tracked = _git_tracked(relative)
            if not tracked:
                raise SpecError(f"declared release surface has no tracked files: {relative}")
            if target.is_symlink() or (not target.is_file() and not target.is_dir()):
                raise SpecError(
                    f"declared release surface is not a regular file or directory: {relative}"
                )
            if target.is_file() and tracked != [relative]:
                raise SpecError(f"declared file surface is not tracked exactly: {relative}")
            for tracked_relative in tracked:
                path = ROOT / tracked_relative
                if path.is_symlink() or not path.is_file():
                    raise SpecError(
                        f"release surfaces may contain only regular files: {tracked_relative}"
                    )
                normalized = tracked_relative.as_posix()
                if normalized in files:
                    raise SpecError(
                        f"release surface file is declared more than once: {normalized}"
                    )
                files.add(normalized)
    if not files:
        raise SpecError("release surfaces expand to no tracked files")
    return sorted(files)


def _sorted_unique_paths(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or value != sorted(value)
        or len(value) != len(set(value))
        or not all(isinstance(item, str) for item in value)
    ):
        raise SpecError(f"{label} must be a sorted unique nonempty path list")
    return value


def validate_spec(path: Path) -> dict[str, Any]:
    value = load(path)
    exact_keys(
        value,
        {
            "schema_version",
            "release_tag",
            "contract_major",
            "change_class",
            "release_surfaces",
            "qualification",
            "publication",
        },
        "release specification",
    )
    if value["schema_version"] != 2 or value["contract_major"] != 5:
        raise SpecError("release specification must declare schema 2 and contract major 5")
    if value["change_class"] != "major" or not TAG.fullmatch(str(value["release_tag"])):
        raise SpecError("release specification must declare one full-semver major release")
    if value["release_tag"] != "v5.0.0":
        raise SpecError("only the corrected v5.0.0 release is publishable")
    if path.name != f"{value['release_tag']}.json" or path.parent.name != "releases":
        raise SpecError("publishable release specification must be the canonical root v5 file")

    surfaces = value["release_surfaces"]
    if not isinstance(surfaces, dict):
        raise SpecError("release_surfaces must be an object")
    exact_keys(surfaces, SURFACE_KEYS, "release_surfaces")
    for category in SURFACE_KEYS:
        _sorted_unique_paths(surfaces[category], f"release_surfaces.{category}")

    reusable = sorted(
        path.relative_to(ROOT).as_posix() for path in WORKFLOWS.glob("reusable-*.yml")
    )
    contracts = sorted(
        (CONTRACTS / f"{Path(workflow).stem}.json").relative_to(ROOT).as_posix()
        for workflow in reusable
    )
    expected = {
        "reusable_workflows": reusable,
        "workflow_contracts": contracts,
        "required_workflows": REQUIRED_WORKFLOWS,
        "repository_home_action": REPOSITORY_HOME_ACTION,
        "release_tools": RELEASE_TOOLS,
        "policy_tools": POLICY_TOOLS,
        "policy_manifest": POLICY_MANIFEST,
    }
    for category, expected_paths in expected.items():
        if surfaces[category] != expected_paths:
            missing = sorted(set(expected_paths) - set(surfaces[category]))
            unexpected = sorted(set(surfaces[category]) - set(expected_paths))
            raise SpecError(
                f"release surface {category} is incomplete; "
                f"missing={missing}, unexpected={unexpected}"
            )
    for contract in contracts:
        if not (ROOT / contract).is_file():
            raise SpecError(f"workflow contract snapshot is absent: {contract}")
    expand_surfaces(value)

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
        raise SpecError(
            "v5 qualification must require all native systems and two Linux rebuilds"
        )

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
    files = {relative: sha256(ROOT / relative) for relative in expand_surfaces(spec)}
    result = {
        "schema_version": 2,
        "release_tag": spec["release_tag"],
        "source_commit": source,
        "release_spec_digest": sha256(spec_path),
        "files": files,
    }
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


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
    if attestation["schema_version"] != 2:
        raise SpecError("unsupported source attestation schema")
    if attestation["release_tag"] != spec["release_tag"]:
        raise SpecError("source attestation release tag does not match")
    if attestation["source_commit"] != expected_source:
        raise SpecError("source attestation commit does not match the annotated tag")
    if attestation["release_spec_digest"] != sha256(spec_path):
        raise SpecError("release specification digest does not match")
    files = attestation["files"]
    expected_files = set(expand_surfaces(spec))
    if not isinstance(files, dict) or set(files) != expected_files:
        raise SpecError(
            "source attestation file map is incomplete or contains unexpected paths"
        )
    for relative, expected_digest in files.items():
        path = ROOT / _safe_relative(relative, "source attestation path")
        if path.is_symlink() or not path.is_file() or sha256(path) != expected_digest:
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
                raise SpecError(
                    "--verify-attestation and --expected-source are required together"
                )
            verify(args.spec, args.verify_attestation, args.expected_source)
        else:
            validate_spec(args.spec)
    except SpecError as exc:
        print(f"release specification rejected: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
