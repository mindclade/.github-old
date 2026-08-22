#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "actions"
    / "validate-repository-home"
    / "validate.py"
)
SPEC = importlib.util.spec_from_file_location("repository_home", MODULE_PATH)
assert SPEC and SPEC.loader
repository_home = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repository_home)
REPOSITORY_ROOT = MODULE_PATH.parents[2]


class RepositoryHomeValidationTest(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / ".github").mkdir()
        (root / "contracts").mkdir()
        (root / "scripts").mkdir()
        (root / "docs" / "assets" / "brand").mkdir(parents=True)
        (root / "docs" / "assets" / "badges").mkdir(parents=True)
        (root / "docs" / "README.md").write_text("# Documentation\n", encoding="utf-8")
        for name in ("mono-wordmark-1080w.png", "mono-wordmark-dark-1080w.png"):
            (root / "docs" / "assets" / "brand" / name).write_bytes(b"png")
        (root / "contracts" / "repository.yaml").write_text(
            """---
schema_version: 1
repository: sample
repository_class: enterprise-control
visibility: private
authority:
  - sample-authority
required_paths:
  - docs/README.md
default_branch: main
change_model: pull-request
""",
            encoding="utf-8",
        )
        (root / "AGENTS.md").write_text("# Agent instructions\n", encoding="utf-8")
        (root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
            """## Contributor authorization

- [ ] I am authorized under a current written agreement with Mindclade, LLC.
- [ ] I identified third-party material and updated LICENSE and NOTICE.
""",
            encoding="utf-8",
        )
        shutil.copyfile(REPOSITORY_ROOT / "LICENSE", root / "LICENSE")
        shutil.copyfile(
            REPOSITORY_ROOT / "CODE_OF_CONDUCT.md", root / "CODE_OF_CONDUCT.md"
        )
        shutil.copyfile(REPOSITORY_ROOT / "LEGAL.md", root / "LEGAL.md")
        shutil.copyfile(
            REPOSITORY_ROOT / "tools" / "third_party_notices.py",
            root / "scripts" / "generate-third-party-notices.py",
        )
        (root / "contracts" / "third-party-materials.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "repository": "mindclade/sample",
                    "inventorySources": [],
                    "materials": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "python3",
                str(root / "scripts" / "generate-third-party-notices.py"),
                "--root",
                str(root),
                "--write",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        common_documents = {
            "CONTRIBUTING.md": """<!-- mindclade-doc: contributing@1 -->

# Contributing to Mindclade · sample

Contributors need a current written agreement and the right and authority to
submit first-party and third-party material.

By submitting or updating a pull request, the contributor represents that the
submission is authorized. Signed commits establish integrity and are not a
substitute for the controlling agreement.
""",
            "SECURITY.md": """<!-- mindclade-doc: security@1 -->

# Mindclade security policy · sample

Do not open a public issue. Use security@mindclade.com or
biosecurity@mindclade.com through an approved private channel.
Response times are operational targets, not contractual service levels. Safe
harbor does not authorize third-party systems or excuse unlawful conduct.
""",
            "SUPPORT.md": """<!-- mindclade-doc: support@1 -->

# Mindclade support · sample

Do not report a vulnerability here; follow SECURITY.md. GitHub has no SLA.
Customer support follows the applicable agreement.
""",
            "GOVERNANCE.md": """<!-- mindclade-doc: governance@1 -->

# Mindclade governance · sample

Changes require review and evidence.
""",
            "CHANGELOG.md": """<!-- mindclade-doc: changelog@1 -->

# Mindclade changelog · sample

## Unreleased
""",
            "NOTICE": """Mindclade, LLC. Proprietary and Third-Party Notice

Document-Control: mindclade-notice@1
Repository: mindclade/sample
SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

Third-party materials retain their own terms. Those terms control.
CODE_OF_CONDUCT.md adapts Contributor Covenant version 2.1 under Creative
Commons Attribution 4.0.
""",
        }
        for name, content in common_documents.items():
            (root / name).write_text(content, encoding="utf-8")
        contract = repository_home.parse_contract(root / "contracts" / "repository.yaml")
        repository_home.write_badges(root, contract)
        (root / "docs" / "assets" / "badges" / "scope.svg").write_text(
            repository_home.badge_svg("scope", "sample"), encoding="utf-8"
        )
        (root / "README.md").write_text(
            """<!-- mindclade-doc: repository-home@2 -->
<!-- Brand source: mindclade/.github-private/mindclade-brand-assets (MONO family). -->
<p align="center"><picture>
<source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/mono-wordmark-dark-1080w.png">
<source media="(prefers-color-scheme: light)" srcset="docs/assets/brand/mono-wordmark-1080w.png">
<img alt="Mindclade." src="docs/assets/brand/mono-wordmark-1080w.png" width="360">
</picture></p>

<p align="center">
<img alt="class: enterprise-control" src="docs/assets/badges/repository-class.svg">
<img alt="visibility: private" src="docs/assets/badges/visibility.svg">
<img alt="change: pull-request" src="docs/assets/badges/change-model.svg">
<img alt="scope: sample" src="docs/assets/badges/scope.svg">
</p>

# Mindclade · Sample

| Repository contract | Value |
| --- | --- |
| Class | `enterprise-control` |
| Visibility | `private` |
| Change model | `pull-request` |
| Authority | `sample-authority` |
| Primary readers | Sample maintainers |
| First success | [Validate the sample](#quick-start) |

## Mission

Orient the reader.

## Authority boundary

### This repository creates

- Sample authority.

### This repository deliberately does not create

- Adjacent state.

## Quick start

Prerequisite: a local checkout.

```sh
true
```

**Success means:** the command exits successfully.

**If it fails:** inspect the command output.

**Safety boundary:** do not mutate external systems.

## Estate position

The diagram shows the repository's position; the authority table is its text equivalent.

```mermaid
%% current: sample %%
%%{init: {"theme":"base","themeVariables":{}}}%%
flowchart LR
    S["sample"]
```

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/` | Documentation. |

## Change path

Use a pull request.

## Documentation and support

- [Documentation](docs/README.md)

## Security

Do not commit secrets.
""",
            encoding="utf-8",
        )
        return root

    def test_valid_repository_home(self) -> None:
        self.assertEqual(repository_home.validate(self.fixture()), [])

    def test_contract_drift_and_remote_image_fail(self) -> None:
        root = self.fixture()
        readme = root / "README.md"
        text = readme.read_text(encoding="utf-8")
        text = text.replace("| Visibility | `private` |", "| Visibility | `internal` |")
        text += '\n<img alt="remote" src="https://img.shields.io/badge/a-b-c">\n'
        readme.write_text(text, encoding="utf-8")
        errors = repository_home.validate(root)
        self.assertTrue(any("Visibility" in error for error in errors))
        self.assertTrue(any("remote README image" in error for error in errors))
        self.assertTrue(any("Shields" in error for error in errors))

    def test_reader_success_path_is_required(self) -> None:
        root = self.fixture()
        readme = root / "README.md"
        text = readme.read_text(encoding="utf-8")
        text = text.replace("| Primary readers | Sample maintainers |\n", "")
        text = text.replace("**If it fails:**", "**Failure route:**")
        readme.write_text(text, encoding="utf-8")
        errors = repository_home.validate(root)
        self.assertTrue(any("primary readers" in error for error in errors))
        self.assertTrue(any("**If it fails:**" in error for error in errors))

    def test_common_document_contract_is_fail_closed(self) -> None:
        root = self.fixture()
        (root / "LICENSE").write_text("short proprietary notice\n", encoding="utf-8")
        notice = root / "NOTICE"
        notice.write_text(
            notice.read_text(encoding="utf-8").replace(
                "Repository: mindclade/sample", "Repository: mindclade/other"
            ),
            encoding="utf-8",
        )
        contributing = root / "CONTRIBUTING.md"
        contributing.write_text(
            contributing.read_text(encoding="utf-8").replace("Signed commits", "Commits"),
            encoding="utf-8",
        )
        errors = repository_home.validate(root)
        self.assertTrue(any("canonical common-document@1" in error for error in errors))
        self.assertTrue(any("Repository: mindclade/sample" in error for error in errors))
        self.assertTrue(any("Signed commits" in error for error in errors))

    def test_legal_reliance_policy_is_fail_closed(self) -> None:
        root = self.fixture()
        legal = root / "LEGAL.md"
        legal.write_text(
            legal.read_text(encoding="utf-8").replace(
                "Documentation is not legal", "Documentation is not professional legal"
            ),
            encoding="utf-8",
        )
        errors = repository_home.validate(root)
        self.assertTrue(any("LEGAL.md differs" in error for error in errors))
        self.assertTrue(any("not legal, medical" in error for error in errors))

    def test_duplicate_root_license_surface_fails(self) -> None:
        root = self.fixture()
        (root / "license-header.txt").write_text(
            "not a standalone license\n", encoding="utf-8"
        )
        errors = repository_home.validate(root)
        self.assertTrue(any("duplicate root license surface" in error for error in errors))

    def test_stale_version_and_broken_link_fail(self) -> None:
        root = self.fixture()
        (root / ".terraform-version").write_text("1.15.9\n", encoding="utf-8")
        readme = root / "README.md"
        text = readme.read_text(encoding="utf-8")
        text += "\nTerraform 1.9.0. [Missing](docs/missing.md)\n"
        readme.write_text(text, encoding="utf-8")
        errors = repository_home.validate(root)
        self.assertTrue(any("pins 1.15.9" in error for error in errors))
        self.assertTrue(any("broken local README link" in error for error in errors))

    def test_identical_local_validator_mirror_passes(self) -> None:
        root = self.fixture()
        mirror = root / "scripts" / "validate-repository-home.py"
        mirror.parent.mkdir(exist_ok=True)
        shutil.copyfile(MODULE_PATH, mirror)
        self.assertEqual(
            repository_home.validate_local_validator(
                MODULE_PATH, root, "scripts/validate-repository-home.py"
            ),
            [],
        )

    def test_modified_local_validator_mirror_fails(self) -> None:
        root = self.fixture()
        mirror = root / "scripts" / "validate-repository-home.py"
        mirror.parent.mkdir(exist_ok=True)
        mirror.write_bytes(MODULE_PATH.read_bytes() + b"\n")
        errors = repository_home.validate_local_validator(
            MODULE_PATH, root, "scripts/validate-repository-home.py"
        )
        self.assertTrue(any("differs from the released action" in error for error in errors))

    def test_missing_and_unsafe_local_validator_paths_fail(self) -> None:
        root = self.fixture()
        missing = repository_home.validate_local_validator(
            MODULE_PATH, root, "scripts/missing.py"
        )
        absolute = repository_home.validate_local_validator(
            MODULE_PATH, root, str(MODULE_PATH)
        )
        escaping = repository_home.validate_local_validator(
            MODULE_PATH, root, "../validate.py"
        )
        self.assertTrue(any("does not exist" in error for error in missing))
        self.assertTrue(any("must be relative" in error for error in absolute))
        self.assertTrue(any("escapes the workspace" in error for error in escaping))

    def test_unqualified_legal_claim_fails(self) -> None:
        root = self.fixture()
        (root / "docs" / "claims.md").write_text(
            "# Claims\n\nThe platform is fully compliant with every applicable standard.\n",
            encoding="utf-8",
        )
        errors = repository_home.validate(root)
        self.assertTrue(
            any("unqualified certification or compliance claim" in error for error in errors)
        )

    def test_scoped_current_legal_claim_approval_passes(self) -> None:
        root = self.fixture()
        (root / "docs" / "claims.md").write_text(
            """# Claims

<!-- mindclade-legal-claim: owner=legal; evidence=LEGAL-1234; scope=specified control set; reviewed=2026-08-21; expires=2099-08-21 -->
The platform is fully compliant within the approved evidence scope.
""",
            encoding="utf-8",
        )
        self.assertEqual(repository_home.validate(root), [])


if __name__ == "__main__":
    unittest.main()
