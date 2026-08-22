#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Select the exact successful policy-bundle publication for one source commit."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA = re.compile(r"^[0-9a-f]{40}$")


class SelectionError(ValueError):
    """The workflow-run response cannot authorize one exact publication."""


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SelectionError("duplicate_json_key")
        result[key] = value
    return result


def load_pages(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicates,
        )
    except OSError as error:
        raise SelectionError("workflow_runs_unreadable") from error
    except UnicodeDecodeError as error:
        raise SelectionError("workflow_runs_invalid_encoding") from error
    except json.JSONDecodeError as error:
        raise SelectionError("workflow_runs_invalid_json") from error
    if not isinstance(payload, list) or not payload:
        raise SelectionError("workflow_run_pages_invalid")
    if not all(isinstance(page, dict) for page in payload):
        raise SelectionError("workflow_run_pages_invalid")
    return payload


def select_run_id(pages: list[dict[str, Any]], source_commit: str) -> int:
    if SHA.fullmatch(source_commit) is None:
        raise SelectionError("source_commit_invalid")

    matches: list[tuple[int, int]] = []
    for page in pages:
        runs = page.get("workflow_runs")
        if not isinstance(runs, list):
            raise SelectionError("workflow_runs_missing")
        for run in runs:
            if not isinstance(run, dict):
                raise SelectionError("workflow_run_invalid")
            run_id = run.get("id")
            run_number = run.get("run_number")
            head_sha = run.get("head_sha")
            if (
                type(run_id) is not int
                or run_id <= 0
                or type(run_number) is not int
                or run_number <= 0
                or not isinstance(head_sha, str)
                or SHA.fullmatch(head_sha) is None
            ):
                raise SelectionError("workflow_run_invalid")
            if head_sha == source_commit:
                matches.append((run_number, run_id))

    if not matches:
        raise SelectionError("publication_run_not_found")
    highest_number = max(run_number for run_number, _ in matches)
    selected = {run_id for run_number, run_id in matches if run_number == highest_number}
    if len(selected) != 1:
        raise SelectionError("publication_run_ambiguous")
    return selected.pop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    try:
        run_id = select_run_id(load_pages(args.runs), args.source_commit)
    except SelectionError as error:
        print(f"policy bundle run selection failed: {error}", file=sys.stderr)
        return 1
    print(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
