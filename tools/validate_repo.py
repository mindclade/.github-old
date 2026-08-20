#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
#
"""Offline structural validation for the Mindclade organization .github repository."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = "Mindclade"
RELEASE = "v3.0.0"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SEMVER_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
MARKER_WORDS = ("T" + "BC", "TO" + "DO", "FIX" + "ME", "CHANGE" + "ME")
MARKER_RE = re.compile(r"\b(?:" + "|".join(MARKER_WORDS) + r")\b")
REQUIRED = {
    ".github/CODEOWNERS",
    ".github/DISCUSSION_TEMPLATE/design-proposal.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/hygiene.yml",
    ".github/workflows/required-repository-policy.yml",
    ".github/workflows/required-security-baseline.yml",
    ".github/workflows/release.yml",
    ".github/workflows/smoke.yml",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "docs/ENTERPRISE_SETUP.md",
    "docs/WIF.md",
    "docs/WORKFLOW_CONTRACTS.md",
    "docs/ACTIONS_SECURITY.md",
    "profile/README.md",
    "BLUEPRINT.md",
    ".github/workflows/reusable-license-headers.yml",
    ".github/workflows/reusable-nix-flake.yml",
    ".github/workflows/reusable-terraform-validate.yml",
    ".github/workflows/reusable-terragrunt-plan.yml",
    ".github/workflows/reusable-artifact-verification.yml",
}

TEXT_SUFFIXES = {
    "", ".css", ".go", ".html", ".json", ".json5", ".lock", ".md", ".nix",
    ".py", ".rs", ".svg", ".toml", ".txt", ".yaml", ".yml",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def iter_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def main() -> int:
    errors: list[str] = []
    files = iter_files()
    names = {rel(path) for path in files}

    for required in sorted(REQUIRED - names):
        fail(errors, f"missing required file: {required}")

    forbidden = {
        ".github/workflows/reusable-slsa-provenance.yml",
        ".github/workflows/scorecard.yml",
        ".github/workflows/stale.yml",
    }
    for name in sorted(forbidden & names):
        fail(errors, f"deprecated workflow must not return: {name}")

    for path in files:
        name = rel(path)
        if path.is_symlink():
            fail(errors, f"symlink is not allowed: {name}")
            continue
        if path.stat().st_size > 1_048_576:
            fail(errors, f"file exceeds 1 MiB: {name}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if text and not text.endswith("\n"):
            fail(errors, f"missing final newline: {name}")
        if name != "tools/validate_repo.py":
            if "mindclade-org" in text:
                fail(errors, f"legacy organization slug in {name}")
            if MARKER_RE.search(text):
                fail(errors, f"unresolved marker in {name}")
            if "v1.0.0" in text:
                fail(errors, f"stale v1 release reference in {name}")
            if "sigstore/cosign" in text or "cosign attest" in text:
                fail(errors, f"legacy public-Sigstore/cosign path in {name}; use GitHub attestations")
        if path.suffix.lower() in {".yml", ".yaml"} and not text.startswith("---\n"):
            fail(errors, f"YAML document must start with '---': {name}")

    for path in sorted(ROOT.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(errors, f"invalid JSON {rel(path)}: {exc}")

    for path in sorted(ROOT.rglob("*.toml")):
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            fail(errors, f"invalid TOML {rel(path)}: {exc}")

    workflow_dir = ROOT / ".github" / "workflows"
    for path in sorted(workflow_dir.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for use in USES_RE.findall(text):
            if use.startswith("./"):
                continue
            target, sep, ref_value = use.rpartition("@")
            if not sep:
                fail(errors, f"unversioned uses reference in {rel(path)}: {use}")
                continue
            if target.startswith(f"{ORG}/.github/.github/workflows/"):
                if not SEMVER_RE.fullmatch(ref_value):
                    fail(errors, f"internal reusable workflow lacks full semver in {rel(path)}: {use}")
                continue
            if not SHA_RE.fullmatch(ref_value):
                fail(errors, f"third-party action is not SHA-pinned in {rel(path)}: {use}")

    templates = ROOT / "workflow-templates"
    for template in sorted(templates.glob("*.yml")):
        sidecar = template.with_suffix(".properties.json")
        if not sidecar.is_file():
            fail(errors, f"workflow template lacks sidecar: {rel(template)}")
        text = template.read_text(encoding="utf-8")
        refs = [use for use in USES_RE.findall(text) if use.startswith(f"{ORG}/.github/")]
        if not refs:
            fail(errors, f"workflow template does not call Mindclade/.github: {rel(template)}")
        for use in refs:
            target, _, version = use.rpartition("@")
            if version != RELEASE:
                fail(errors, f"starter template must pin {RELEASE}: {rel(template)} uses {version}")
            prefix = f"{ORG}/.github/"
            local = target.removeprefix(prefix)
            if not (ROOT / local).is_file():
                fail(errors, f"starter template references missing workflow: {local}")

    for markdown in sorted(ROOT.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
            destination = match.group(1).split("#", 1)[0]
            if not destination or "://" in destination or destination.startswith("mailto:"):
                continue
            target = (markdown.parent / destination).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                fail(errors, f"markdown link escapes repository in {rel(markdown)}: {destination}")
                continue
            if not target.exists():
                fail(errors, f"broken local markdown link in {rel(markdown)}: {destination}")

    contract_check = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_workflow_contracts.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if contract_check.returncode != 0:
        detail = contract_check.stderr.strip() or contract_check.stdout.strip()
        fail(errors, f"workflow contract validation failed: {detail}")

    if errors:
        print("repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"repository validation passed: {len(files)} files checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
