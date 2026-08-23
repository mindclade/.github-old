#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Build, verify, and synchronize the deterministic Mindclade policy bundle."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = DEFAULT_SOURCE_ROOT / "contracts" / "policy-bundle" / "manifest.json"
DEFAULT_HISTORY = DEFAULT_SOURCE_ROOT / "contracts" / "policy-bundle" / "version-history.json"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
VERSION_RE = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[1-9][0-9]*$")
EXPECTED_TOP_LEVEL = {
    "schemaVersion",
    "bundleId",
    "version",
    "effectiveDate",
    "canonicalRepository",
    "licenseExpression",
    "signature",
    "artifacts",
}
EXPECTED_ARTIFACT = {"name", "source", "sha256", "mediaType", "distributions"}
EXPECTED_DISTRIBUTION = {"repository", "path"}
EXPECTED_HISTORY = {"schemaVersion", "bundleId", "versions"}
EXPECTED_HISTORY_VERSION = {
    "version",
    "effectiveDate",
    "manifestSha256",
    "status",
}
MANAGED_REPOSITORIES = {
    ".github",
    ".github-private",
    "bootstrap",
    "github-config",
    "gitops",
    "infrastructure-live",
    "mindclade-internal-monorepo",
}
POLICY_MANIFEST_TARGET = Path("contracts/policy-bundle/manifest.json")


class PolicyBundleError(ValueError):
    """A policy bundle or synchronization target violated its contract."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise PolicyBundleError(f"{label} must be a string-keyed object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise PolicyBundleError(
            f"{label} keys must be exactly {sorted(expected)}; got {sorted(value)}"
        )


def _safe_relative(raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise PolicyBundleError(f"{label} must be a nonempty POSIX relative path")
    path = Path(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PolicyBundleError(f"{label} must be a normalized relative path")
    return path


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyBundleError(f"cannot load manifest {path}: {exc}") from exc
    manifest = _mapping(value, "manifest")
    _exact_keys(manifest, EXPECTED_TOP_LEVEL, "manifest")
    if manifest["schemaVersion"] != 1:
        raise PolicyBundleError("manifest schemaVersion must be 1")
    if manifest["bundleId"] != "mindclade-policy-bundle":
        raise PolicyBundleError("manifest bundleId is not canonical")
    if not isinstance(manifest["version"], str) or not VERSION_RE.fullmatch(
        manifest["version"]
    ):
        raise PolicyBundleError("manifest version must be YYYY.MM.DD.N")
    if manifest["canonicalRepository"] != "mindclade/.github":
        raise PolicyBundleError("canonicalRepository must be mindclade/.github")
    if manifest["licenseExpression"] != "LicenseRef-Mindclade-Proprietary":
        raise PolicyBundleError("licenseExpression must use the Mindclade SPDX LicenseRef")
    signature = _mapping(manifest["signature"], "signature")
    _exact_keys(
        signature,
        {"required", "method", "workflow", "protectedEnvironment"},
        "signature",
    )
    if signature != {
        "required": True,
        "method": "github-artifact-attestation-sigstore",
        "workflow": ".github/workflows/publish-policy-bundle.yml",
        "protectedEnvironment": "workflow-release-security",
    }:
        raise PolicyBundleError("signature contract is not the protected canonical contract")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise PolicyBundleError("artifacts must be a nonempty list")
    names: set[str] = set()
    sources: set[Path] = set()
    targets: set[tuple[str, Path]] = set()
    for index, raw_artifact in enumerate(artifacts):
        artifact = _mapping(raw_artifact, f"artifacts[{index}]")
        _exact_keys(artifact, EXPECTED_ARTIFACT, f"artifacts[{index}]")
        name = artifact["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]+", name):
            raise PolicyBundleError(f"artifacts[{index}].name is malformed")
        if name in names:
            raise PolicyBundleError(f"duplicate artifact name: {name}")
        names.add(name)
        source = _safe_relative(artifact["source"], f"artifacts[{index}].source")
        if source in sources:
            raise PolicyBundleError(f"duplicate artifact source: {source}")
        sources.add(source)
        digest = artifact["sha256"]
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise PolicyBundleError(f"artifacts[{index}].sha256 is malformed")
        distributions = artifact["distributions"]
        if not isinstance(distributions, list):
            raise PolicyBundleError(f"artifacts[{index}].distributions must be a list")
        for target_index, raw_distribution in enumerate(distributions):
            distribution = _mapping(
                raw_distribution, f"artifacts[{index}].distributions[{target_index}]"
            )
            _exact_keys(
                distribution,
                EXPECTED_DISTRIBUTION,
                f"artifacts[{index}].distributions[{target_index}]",
            )
            repository = distribution["repository"]
            if repository not in MANAGED_REPOSITORIES:
                raise PolicyBundleError(f"unknown distribution repository: {repository}")
            target = _safe_relative(
                distribution["path"],
                f"artifacts[{index}].distributions[{target_index}].path",
            )
            key = (repository, target)
            if key in targets:
                raise PolicyBundleError(
                    f"multiple artifacts target {repository}/{target.as_posix()}"
                )
            targets.add(key)
    return manifest


def load_version_history(path: Path = DEFAULT_HISTORY) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyBundleError(f"cannot load version history {path}: {exc}") from exc
    history = _mapping(value, "version history")
    _exact_keys(history, EXPECTED_HISTORY, "version history")
    if history["schemaVersion"] != 1:
        raise PolicyBundleError("version history schemaVersion must be 1")
    if history["bundleId"] != "mindclade-policy-bundle":
        raise PolicyBundleError("version history bundleId is not canonical")
    versions = history["versions"]
    if not isinstance(versions, list) or not versions:
        raise PolicyBundleError("version history must contain at least one version")
    previous = ""
    for index, raw_record in enumerate(versions):
        record = _mapping(raw_record, f"versions[{index}]")
        _exact_keys(record, EXPECTED_HISTORY_VERSION, f"versions[{index}]")
        version = record["version"]
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            raise PolicyBundleError(f"versions[{index}].version must be YYYY.MM.DD.N")
        if previous and version <= previous:
            raise PolicyBundleError("version history must be strictly increasing and unique")
        previous = version
        if not isinstance(record["effectiveDate"], str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", record["effectiveDate"]
        ):
            raise PolicyBundleError(f"versions[{index}].effectiveDate is malformed")
        if not isinstance(record["manifestSha256"], str) or not SHA256_RE.fullmatch(
            record["manifestSha256"]
        ):
            raise PolicyBundleError(f"versions[{index}].manifestSha256 is malformed")
        if record["status"] not in {"candidate", "published", "superseded-unpublished"}:
            raise PolicyBundleError(f"versions[{index}].status is invalid")
    return history


def verify_version_history(
    history: dict[str, Any],
    manifest_path: Path,
    manifest: dict[str, Any],
    baseline_history: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    records = history["versions"]
    matches = [record for record in records if record["version"] == manifest["version"]]
    if len(matches) != 1:
        errors.append("current policy version must occur exactly once in version history")
    else:
        record = matches[0]
        actual_digest = sha256(manifest_path)
        if record["manifestSha256"] != actual_digest:
            errors.append(
                "policy manifest changed without a version bump: "
                f"{actual_digest} != {record['manifestSha256']}"
            )
        if record["effectiveDate"] != manifest["effectiveDate"]:
            errors.append("policy manifest effectiveDate differs from version history")
    if records[-1]["version"] != manifest["version"]:
        errors.append("current policy version must be the final history record")
    if baseline_history is not None:
        baseline_records = baseline_history.get("versions", [])
        if records[: len(baseline_records)] != baseline_records:
            errors.append("policy version history is not append-only")
    return errors


def history_at_git_ref(source_root: Path, ref: str) -> dict[str, Any] | None:
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise PolicyBundleError("baseline ref must be a full 40-character commit SHA")
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:contracts/policy-bundle/version-history.json"],
            cwd=source_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise PolicyBundleError(f"cannot inspect baseline version history: {exc}") from exc
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PolicyBundleError(f"baseline version history is invalid: {exc}") from exc
    return _mapping(value, "baseline version history")


def verify_sources(manifest: dict[str, Any], source_root: Path) -> list[str]:
    errors: list[str] = []
    resolved_root = source_root.resolve()
    for artifact in manifest["artifacts"]:
        relative = Path(artifact["source"])
        source = (resolved_root / relative).resolve()
        try:
            source.relative_to(resolved_root)
        except ValueError:
            errors.append(f"source escapes canonical repository: {relative}")
            continue
        if not source.is_file():
            errors.append(f"missing canonical artifact: {relative}")
            continue
        actual = sha256(source)
        if actual != artifact["sha256"]:
            errors.append(
                f"canonical artifact digest drift: {relative}: {actual} != {artifact['sha256']}"
            )
    return errors


def distributions_for(manifest: dict[str, Any], repository: str) -> list[tuple[dict[str, Any], Path]]:
    if repository not in MANAGED_REPOSITORIES:
        raise PolicyBundleError(f"repository is outside the managed set: {repository}")
    result: list[tuple[dict[str, Any], Path]] = []
    for artifact in manifest["artifacts"]:
        for distribution in artifact["distributions"]:
            if distribution["repository"] == repository:
                result.append((artifact, Path(distribution["path"])))
    return result


def verify_target(
    manifest: dict[str, Any], source_root: Path, repository: str, target_root: Path
) -> list[str]:
    errors: list[str] = []
    resolved_target = target_root.resolve()
    contract = resolved_target / "contracts" / "repository.yaml"
    if not contract.is_file() or not re.search(
        rf"^repository:\s*{re.escape(repository)}\s*$",
        contract.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        errors.append(f"target repository contract does not identify {repository}")
        return errors
    distributed_manifest = resolved_target / POLICY_MANIFEST_TARGET
    canonical_manifest = source_root.resolve() / "contracts" / "policy-bundle" / "manifest.json"
    if not distributed_manifest.is_file():
        errors.append(f"missing distributed artifact: {repository}/{POLICY_MANIFEST_TARGET}")
    elif distributed_manifest.read_bytes() != canonical_manifest.read_bytes():
        errors.append(
            f"distributed artifact drift: {repository}/{POLICY_MANIFEST_TARGET}"
        )
    for artifact, relative in distributions_for(manifest, repository):
        target = (resolved_target / relative).resolve()
        try:
            target.relative_to(resolved_target)
        except ValueError:
            errors.append(f"distribution path escapes target: {relative}")
            continue
        if not target.is_file():
            errors.append(f"missing distributed artifact: {repository}/{relative}")
            continue
        actual = sha256(target)
        if actual != artifact["sha256"]:
            errors.append(
                f"distributed artifact drift: {repository}/{relative}: "
                f"{actual} != {artifact['sha256']}"
            )
    return errors


def synchronize(
    manifest: dict[str, Any], source_root: Path, repository: str, target_root: Path
) -> list[Path]:
    errors = verify_sources(manifest, source_root)
    if errors:
        raise PolicyBundleError("; ".join(errors))
    changed: list[Path] = []
    resolved_target = target_root.resolve()
    canonical_manifest = source_root.resolve() / "contracts" / "policy-bundle" / "manifest.json"
    distributed_manifest = resolved_target / POLICY_MANIFEST_TARGET
    if not distributed_manifest.is_file() or distributed_manifest.read_bytes() != canonical_manifest.read_bytes():
        distributed_manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(canonical_manifest, distributed_manifest)
        changed.append(POLICY_MANIFEST_TARGET)
    for artifact, relative in distributions_for(manifest, repository):
        source = source_root.resolve() / artifact["source"]
        target = (resolved_target / relative).resolve()
        try:
            target.relative_to(resolved_target)
        except ValueError as exc:
            raise PolicyBundleError(f"distribution path escapes target: {relative}") from exc
        if target.is_file() and target.read_bytes() == source.read_bytes():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        changed.append(relative)
    remaining = verify_target(manifest, source_root, repository, target_root)
    if remaining:
        raise PolicyBundleError("; ".join(remaining))
    return changed


def build_bundle(
    manifest_path: Path, manifest: dict[str, Any], source_root: Path, output: Path
) -> str:
    errors = verify_sources(manifest, source_root)
    if errors:
        raise PolicyBundleError("; ".join(errors))
    entries = [(manifest_path, Path("manifest.json"))]
    entries.extend(
        (source_root / artifact["source"], Path(artifact["source"]))
        for artifact in manifest["artifacts"]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for source, name in sorted(entries, key=lambda item: item[1].as_posix()):
            payload = source.read_bytes()
            info = tarfile.TarInfo(name.as_posix())
            info.size = len(payload)
            info.mode = 0o644
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(payload))
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(buffer.getvalue())
    digest = sha256(output)
    checksum = output.with_name(output.name + ".sha256")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--repository")
    verify_parser.add_argument("--target-root", type=Path)
    verify_parser.add_argument("--baseline-ref")

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--repository", required=True)
    sync_parser.add_argument("--target-root", type=Path, required=True)
    sync_parser.add_argument("--write", action="store_true")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        source_errors = verify_sources(manifest, args.source_root)
        if source_errors:
            raise PolicyBundleError("; ".join(source_errors))
        if args.command == "verify":
            history = load_version_history(
                args.source_root / "contracts" / "policy-bundle" / "version-history.json"
            )
            baseline_history = (
                history_at_git_ref(args.source_root, args.baseline_ref)
                if args.baseline_ref
                else None
            )
            history_errors = verify_version_history(
                history, args.manifest, manifest, baseline_history
            )
            if history_errors:
                raise PolicyBundleError("; ".join(history_errors))
            if bool(args.repository) != bool(args.target_root):
                raise PolicyBundleError("--repository and --target-root must be supplied together")
            errors = (
                verify_target(
                    manifest, args.source_root, args.repository, args.target_root
                )
                if args.repository
                else []
            )
            if errors:
                raise PolicyBundleError("; ".join(errors))
            print(f"policy bundle verified: {manifest['version']}")
        elif args.command == "sync":
            if not args.write:
                errors = verify_target(
                    manifest, args.source_root, args.repository, args.target_root
                )
                if errors:
                    raise PolicyBundleError("; ".join(errors))
                print(f"policy bundle target is current: {args.repository}")
            else:
                changed = synchronize(
                    manifest, args.source_root, args.repository, args.target_root
                )
                print(
                    json.dumps(
                        {
                            "repository": args.repository,
                            "version": manifest["version"],
                            "changed": [path.as_posix() for path in changed],
                        },
                        sort_keys=True,
                    )
                )
        else:
            digest = build_bundle(
                args.manifest.resolve(),
                manifest,
                args.source_root.resolve(),
                args.output.resolve(),
            )
            print(f"{digest}  {args.output}")
    except PolicyBundleError as exc:
        print(f"policy bundle validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
