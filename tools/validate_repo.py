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
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    print(
        "tools/validate_repo.py requires Python 3.11 or newer; "
        "run `nix develop .#ci --command make validate`.",
        file=sys.stderr,
    )
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
ORG = "mindclade"
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
    ".github/workflows/publish-release.yml",
    ".github/workflows/smoke.yml",
    "AGENTS.md",
    "actions/validate-repository-home/action.yml",
    "actions/validate-repository-home/README.md",
    "actions/validate-repository-home/validate.py",
    "actions/validate-repository-home/verify_adoption.py",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "GOVERNANCE.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "tests/test_repository_home.py",
    "docs/ENTERPRISE_SETUP.md",
    "docs/WIF.md",
    "docs/WORKFLOW_CONTRACTS.md",
    "docs/ACTIONS_SECURITY.md",
    "docs/common-document-contract.md",
    "docs/policy-bundle.md",
    "profile/README.md",
    "BLUEPRINT.md",
    ".github/workflows/reusable-license-headers.yml",
    ".github/workflows/reusable-nix-flake.yml",
    ".github/workflows/reusable-nix-qualification.yml",
    ".github/workflows/reusable-terraform-validate.yml",
    ".github/workflows/reusable-terragrunt-plan.yml",
    ".github/workflows/reusable-artifact-verification.yml",
    ".github/workflows/reusable-binauthz-sign.yml",
    ".github/workflows/reusable-arc-wif-canary.yml",
    ".github/workflows/reusable-arc-oci-build.yml",
    ".github/workflows/reusable-arc-oci-qualify.yml",
    ".github/workflows/reusable-arc-qualification-attest.yml",
    ".github/workflows/reusable-gitops-promote.yml",
    ".github/workflows/reusable-dr-evidence.yml",
    "schemas/drill-report-v2.schema.json",
    "tools/validate_drill_report.py",
    "tests/test_drill_report.py",
    "contracts/releases/release-spec.schema.json",
    "contracts/releases/retired/v4.0.0.json",
    "contracts/releases/v5.0.0.json",
    "tools/validate-release-spec.py",
    "tests/test_release_spec.py",
    "contracts/policy-bundle/acceptance-record.schema.json",
    "contracts/policy-bundle/adoption-record.schema.json",
    "contracts/policy-bundle/manifest.json",
    "contracts/policy-bundle/policy-bundle.schema.json",
    "contracts/third-party-materials.json",
    "THIRD_PARTY_NOTICES.md",
    "tools/policy_bundle.py",
    "tools/policy_adoption.py",
    "tools/validate_pr_policy.py",
    "tools/third_party_notices.py",
    "tools/enrich_spdx_license.py",
    "tests/test_third_party_notices.py",
    "tests/test_spdx_license.py",
    "tests/test_policy_adoption.py",
    "tests/test_pr_policy.py",
}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".go",
    ".html",
    ".json",
    ".json5",
    ".lock",
    ".md",
    ".nix",
    ".py",
    ".rs",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEMPLATE_RENDER_BASES = {
    "docs/templates/documentation-home.md": ROOT / "docs",
    "docs/templates/repository-home.md": ROOT,
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def iter_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts
    )


def main() -> int:
    errors: list[str] = []
    files = iter_files()
    names = {rel(path) for path in files}

    for required in sorted(REQUIRED - names):
        fail(errors, f"missing required file: {required}")

    forbidden = {
        "contracts/releases/v4.0.0.json",
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
            # v1.0.0 remains a valid first application release ID in rollback-lineage
            # contracts. Reject only stale shared-workflow pins, not that domain value.
            if re.search(r"@(?:refs/tags/)?v1\.0\.0\b", text):
                fail(errors, f"stale v1 workflow release pin in {name}")
            if "sigstore/cosign" in text or "cosign attest" in text:
                fail(
                    errors,
                    f"legacy public-Sigstore/cosign path in {name}; use GitHub attestations",
                )
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
        if "-lock=false" in text:
            fail(errors, f"Terraform state locking is disabled in {rel(path)}")
        for use in USES_RE.findall(text):
            if use.startswith("./"):
                continue
            target, sep, ref_value = use.rpartition("@")
            if not sep:
                fail(errors, f"unversioned uses reference in {rel(path)}: {use}")
                continue
            if target.startswith(f"{ORG}/.github/.github/workflows/"):
                if not SEMVER_RE.fullmatch(ref_value):
                    fail(
                        errors,
                        f"internal reusable workflow lacks full semver in {rel(path)}: {use}",
                    )
                continue
            if not SHA_RE.fullmatch(ref_value):
                fail(
                    errors,
                    f"third-party action is not SHA-pinned in {rel(path)}: {use}",
                )

    templates = ROOT / "workflow-templates"
    for template in sorted(templates.glob("*.yml")):
        sidecar = template.with_suffix(".properties.json")
        if not sidecar.is_file():
            fail(errors, f"workflow template lacks sidecar: {rel(template)}")
        text = template.read_text(encoding="utf-8")
        refs = [
            use for use in USES_RE.findall(text) if use.startswith(f"{ORG}/.github/")
        ]
        if not refs:
            fail(
                errors,
                f"workflow template does not call mindclade/.github: {rel(template)}",
            )
        for use in refs:
            target, _, version = use.rpartition("@")
            if version != RELEASE:
                fail(
                    errors,
                    f"starter template must pin {RELEASE}: {rel(template)} uses {version}",
                )
            prefix = f"{ORG}/.github/"
            local = target.removeprefix(prefix)
            if not (ROOT / local).is_file():
                fail(errors, f"starter template references missing workflow: {local}")

    build_workflow = (workflow_dir / "reusable-oci-build.yml").read_text(
        encoding="utf-8"
    )
    signer_workflow = (workflow_dir / "reusable-binauthz-sign.yml").read_text(
        encoding="utf-8"
    )
    terraform_plan_workflow = (workflow_dir / "reusable-tf-plan.yml").read_text(
        encoding="utf-8"
    )
    if "-lock-timeout=20m" not in terraform_plan_workflow:
        fail(errors, "reusable Terraform plans must wait for the backend state lock")
    if "binauthz attestations sign-and-create" in build_workflow:
        fail(
            errors,
            "OCI builder must not create Binary Authorization deployment attestations",
        )
    for legacy_input in (
        "      attestor:\n",
        "      attestor-project:\n",
        "      attestor-key:\n",
    ):
        if legacy_input in build_workflow:
            fail(
                errors,
                f"OCI builder retains forbidden signing input: {legacy_input.strip()}",
            )
    signer_requirements = {
        "    environment: release": "protected release environment",
        "vars.WIF_PROVIDER_SIGNER": "governed signer WIF provider",
        "vars.SA_ARTIFACT_SIGNER": "dedicated signer service account",
        "vars.BINAUTHZ_BUILD_ATTESTOR_PROJECT": "ARC build/provenance project",
        "vars.BINAUTHZ_BUILD_ATTESTOR": "ARC build/provenance attestor",
        "vars.BINAUTHZ_QUALIFICATION_ATTESTOR_PROJECT": "independent qualification project",
        "vars.BINAUTHZ_QUALIFICATION_ATTESTOR": "independent qualification attestor",
        "vars.BINAUTHZ_DEPLOYMENT_ATTESTOR_PROJECT": "deployment attestor project",
        "vars.BINAUTHZ_DEPLOYMENT_ATTESTOR": "deployment attestor",
        "vars.BINAUTHZ_DEPLOYMENT_ATTESTOR_KEY_VERSION": "immutable deployment signing key version",
        "build, qualification, and deployment attestors must be distinct": "three distinct evidence roots",
        'version: "580.0.0"': "exact Google Cloud CLI version",
        "gcloud beta container binauthz attestations sign-and-create": "documented KMS Binary Authorization signing operation",
        "--validate": "post-signature attestor validation",
        ":validateAttestationOccurrence": "cryptographic upstream-attestation validation",
        '.result == "VERIFIED"': "fail-closed signature-verification result check",
    }
    for needle, control in signer_requirements.items():
        if needle not in signer_workflow:
            fail(errors, f"Binary Authorization signer lacks {control}")
    for required_claim in (
        '[ "$GITHUB_EVENT_NAME" = push ]',
        '[ "$GITHUB_REF" = refs/heads/main ]',
        '[ "$GITHUB_REPOSITORY" = mindclade/mindclade-internal-monorepo ]',
    ):
        if required_claim not in signer_workflow:
            fail(errors, f"Binary Authorization signer lacks runtime claim: {required_claim}")
    for caller_selected_input in (
        "      service-account:\n",
        "      workload-identity-provider:\n",
    ):
        if caller_selected_input in signer_workflow:
            fail(
                errors,
                f"Binary Authorization signer exposes forbidden caller input: {caller_selected_input.strip()}",
            )
    for forbidden_authority in (
        "gh attestation",
        "--signer-workflow",
        "--bundle-from-oci",
        "attestations: read",
        "vars.BINAUTHZ_ATTESTOR_PROJECT",
        "vars.BINAUTHZ_ATTESTOR_KEY_VERSION",
    ):
        if forbidden_authority in signer_workflow:
            fail(
                errors,
                f"Binary Authorization signer retains forbidden/ambiguous trust authority: {forbidden_authority}",
            )
    if "gcloud container binauthz attestations sign-and-create" in signer_workflow:
        fail(
            errors,
            "Binary Authorization signer uses the unsupported stable-track spelling",
        )

    arc_workflows = {
        path.name: path.read_text(encoding="utf-8")
        for path in workflow_dir.glob("reusable-arc-*.yml")
    }
    arc_workflows["reusable-gitops-promote.yml"] = (
        workflow_dir / "reusable-gitops-promote.yml"
    ).read_text(encoding="utf-8")
    for name, text in arc_workflows.items():
        for required_claim in ("= push ]", "= refs/heads/main ]"):
            if required_claim not in text:
                fail(errors, f"{name} lacks trusted-main runtime check: {required_claim}")
        if "mindclade/mindclade-internal-monorepo" not in text:
            fail(errors, f"{name} lacks the exact artifact-authority repository check")
        if "workflow_dispatch:" in text or "repository_dispatch:" in text:
            fail(errors, f"{name} exposes a manual/API authority trigger")

    for name in (
        "reusable-arc-oci-build.yml",
        "reusable-arc-oci-qualify.yml",
        "reusable-arc-qualification-attest.yml",
    ):
        if "actions/checkout@" not in arc_workflows[name]:
            fail(errors, f"{name} does not perform an exact source checkout")
        if "ref: ${{ github.sha }}" not in arc_workflows[name]:
            fail(errors, f"{name} does not pin checkout to the platform SHA")
        if (
            "cachix/install-nix-action@630ae543ea3a38a9a4166f03376c02c50f408342"
            not in arc_workflows[name]
            or "install_options: --no-daemon" not in arc_workflows[name]
        ):
            fail(errors, f"{name} does not provision pinned Nix for its ARC container")

    expected_arc_runner_labels = {
        "reusable-arc-wif-canary.yml": "mindclade-arc-canary",
        "reusable-arc-oci-build.yml": "mindclade-arc-build-cpu",
        "reusable-arc-oci-qualify.yml": "mindclade-arc-qualify-cpu",
        "reusable-arc-qualification-attest.yml": "mindclade-arc-qualify-cpu",
    }
    for name, runner_label in expected_arc_runner_labels.items():
        if f"runs-on: {runner_label}" not in arc_workflows[name]:
            fail(
                errors,
                f"{name} does not use its provisioned ARC scale-set label: {runner_label}",
            )

    builder_workflow = arc_workflows["reusable-arc-oci-build.yml"]
    for required_builder_value in (
        "vars.ARTIFACT_REGISTRY_HOST",
        "vars.ARTIFACT_REGISTRY_DR_HOST",
        "vars.CI_PROJECT_ID",
        "vars.BINAUTHZ_BUILD_ATTESTOR_PROJECT",
        "vars.BINAUTHZ_BUILD_ATTESTOR",
        "vars.BINAUTHZ_BUILD_ATTESTOR_KEY_VERSION",
        'gcloud auth configure-docker "$ARTIFACT_REGISTRY_HOST" --quiet',
        '[ "$ARTIFACT_REGISTRY_HOST" = us-central1-docker.pkg.dev ]',
        '[ "$ARTIFACT_REGISTRY_DR_HOST" = us-east4-docker.pkg.dev ]',
    ):
        if required_builder_value not in builder_workflow:
            fail(
                errors,
                "ARC builder does not export/configure required immutable release value: "
                f"{required_builder_value}",
            )

    promoter_workflow = arc_workflows["reusable-gitops-promote.yml"]
    for required_promoter_value in (
        "[ \"$GITHUB_REPOSITORY\" = mindclade/mindclade-internal-monorepo ]",
        "google-github-actions/setup-gcloud@aa5489c8933f4cc7a4f7d45035b3b1440c9c10db",
        'version: "580.0.0"',
        "cachix/install-nix-action@630ae543ea3a38a9a4166f03376c02c50f408342",
        "nix develop .#ci --command python3 scripts/create-release-promotion.py",
    ):
        if required_promoter_value not in promoter_workflow:
            fail(
                errors,
                f"GitOps promoter lacks an exact runtime prerequisite: {required_promoter_value}",
            )

    for markdown in sorted(ROOT.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        link_base = TEMPLATE_RENDER_BASES.get(rel(markdown), markdown.parent)
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
            destination = match.group(1).split("#", 1)[0]
            if (
                not destination
                or "://" in destination
                or destination.startswith("mailto:")
            ):
                continue
            target = (link_base / destination).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                fail(
                    errors,
                    f"markdown link escapes repository in {rel(markdown)}: {destination}",
                )
                continue
            if not target.exists():
                fail(
                    errors,
                    f"broken local markdown link in {rel(markdown)}: {destination}",
                )

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
