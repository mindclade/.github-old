#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
<<<<<<< HEAD
import shutil
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


class RepositoryHomeValidationTest(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "contracts").mkdir()
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

## Mission

Orient the reader.

## Authority boundary

### This repository creates

- Sample authority.

### This repository deliberately does not create

- Adjacent state.

## Quick start

```sh
true
```

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
        mirror.parent.mkdir()
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
        mirror.parent.mkdir()
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
||||||| parent of 0ed0a1a (feat(ci): harden enterprise workflow platform)
=======
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


class RepositoryHomeValidationTest(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "contracts").mkdir()
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

## Mission

Orient the reader.

## Authority boundary

### This repository creates

- Sample authority.

### This repository deliberately does not create

- Adjacent state.

## Quick start

```sh
true
```

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
>>>>>>> 0ed0a1a (feat(ci): harden enterprise workflow platform)


if __name__ == "__main__":
    unittest.main()
