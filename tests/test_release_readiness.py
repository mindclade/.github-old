#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import re
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_release_readiness", ROOT / "tools" / "validate_release_readiness.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


DOCS = ROOT / "docs"
TAG_COMMAND = re.compile(r"^\s*git tag -a\b.*$", re.MULTILINE)


class ReleaseReadinessTest(unittest.TestCase):
    def manifest(self) -> dict[str, object]:
        return json.loads(
            (ROOT / "contracts" / "releases" / "v4.0.0.json").read_text(
                encoding="utf-8"
            )
        )

    def test_checked_in_source_evidence_is_valid(self) -> None:
        errors, tag_status = MODULE.validate_manifest(self.manifest(), ROOT)
        self.assertEqual(errors, [])
        self.assertIn(tag_status, {"absent", "present"})

    def test_tampered_required_file_digest_is_rejected(self) -> None:
        manifest = self.manifest()
        manifest["required_files"]["CHANGELOG.md"] = "sha256:" + "0" * 64
        errors, _ = MODULE.validate_manifest(manifest, ROOT)
        self.assertTrue(any("CHANGELOG.md mismatch" in error for error in errors))

    def test_connected_evidence_cannot_be_marked_optional(self) -> None:
        manifest = self.manifest()
        manifest["connected_evidence"]["required"] = False
        errors, _ = MODULE.validate_manifest(manifest, ROOT)
        self.assertIn(
            "connected evidence must remain required and enumerate every release gate",
            errors,
        )

    # --- release lineage -------------------------------------------------------------------

    def repository(self, squashed: bool) -> tuple[Path, str]:
        """A repository whose reviewed commit either is or is not on main.

        `squashed=True` reproduces what a squash merge does to a release anchor: the reviewed
        commit still exists — a branch keeps it alive, exactly as stale local branches and
        rescue tags did in the real incident — but main descends from its parent instead.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)

        def run(*arguments: str) -> str:
            return subprocess.run(
                ["git", "-C", str(root), *arguments],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.strip()

        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(root)], check=True, capture_output=True
        )
        run("config", "user.email", "release-test@mindclade.com")
        run("config", "user.name", "release test")
        (root / "file.txt").write_text("base\n", encoding="utf-8")
        run("add", "-A")
        run("commit", "-qm", "base")

        run("checkout", "-qb", "review")
        (root / "file.txt").write_text("reviewed\n", encoding="utf-8")
        run("add", "-A")
        run("commit", "-qm", "reviewed change")
        reviewed = run("rev-parse", "HEAD")

        run("checkout", "-q", "main")
        if squashed:
            # An equivalent tree, but parented on base — the reviewed commit is orphaned.
            (root / "file.txt").write_text("reviewed\n", encoding="utf-8")
            run("add", "-A")
            run("commit", "-qm", "reviewed change (#1)")
        else:
            run("merge", "-q", "--no-ff", "-m", "merge review (#1)", "review")
        return root, reviewed

    def test_source_commit_on_mainline_is_an_ancestor(self) -> None:
        root, reviewed = self.repository(squashed=False)
        self.assertEqual(MODULE.lineage_status(root, reviewed, "refs/heads/main"), "ancestor")

    def test_source_commit_orphaned_by_squash_merge_is_rejected(self) -> None:
        root, reviewed = self.repository(squashed=True)
        self.assertEqual(MODULE.lineage_status(root, reviewed, "refs/heads/main"), "diverged")

        manifest = self.manifest()
        manifest["source_commit"] = reviewed
        manifest["required_tag"]["target_commit"] = reviewed
        errors, _ = MODULE.validate_manifest(manifest, root, mainline_ref="refs/heads/main")
        self.assertTrue(
            any("is not an ancestor of" in error for error in errors),
            f"squash-orphaned source_commit was accepted: {errors}",
        )

    def test_absent_mainline_is_reported_rather_than_silently_passed(self) -> None:
        self.assertEqual(MODULE.lineage_status(ROOT, "0" * 40, ""), "unverified")

    def test_checked_in_source_commit_is_still_on_mainline(self) -> None:
        mainline = MODULE.resolve_mainline(ROOT)
        if not mainline:
            self.skipTest("no origin/main or main ref in this checkout")
        commit = str(self.manifest()["source_commit"])
        self.assertEqual(
            MODULE.lineage_status(ROOT, commit, mainline),
            "ancestor",
            f"{commit} is no longer reachable from {mainline}",
        )

    # --- release guides --------------------------------------------------------------------

    def test_release_guides_tag_an_explicit_commit(self) -> None:
        """`git tag -a v -m msg` tags whatever is checked out.

        The v4.0.0 anchor was a commit main did not point at, so a guide that omits the
        commit operand tags the wrong object and the operator has no way to notice.
        """
        offenders: list[str] = []
        for document in sorted(DOCS.rglob("*.md")):
            for line in TAG_COMMAND.findall(document.read_text(encoding="utf-8")):
                tokens = shlex.split(line.strip(), comments=True)
                # git tag -a <version> -m <message> [<commit>]
                if "-m" not in tokens:
                    continue
                if len(tokens) <= tokens.index("-m") + 2:
                    offenders.append(f"{document.relative_to(ROOT)}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "release guides must tag an explicit commit-ish:\n  " + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()

