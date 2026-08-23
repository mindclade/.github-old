#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Extract one exact, non-empty full-semver changelog section."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FULL_SEMVER = re.compile(r"^v[0-9]+[.][0-9]+[.][0-9]+$")


class ReleaseNotesError(ValueError):
    """The requested changelog section is absent or ambiguous."""


def extract(contents: str, tag: str) -> str:
    if not FULL_SEMVER.fullmatch(tag):
        raise ReleaseNotesError("tag must be a stable vMAJOR.MINOR.PATCH release")
    lines = contents.splitlines()
    heading = f"## {tag}"
    matches = [index for index, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        raise ReleaseNotesError(
            f"CHANGELOG.md must contain exactly one exact '{heading}' heading"
        )
    start = matches[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    notes = "\n".join(lines[start:end]).strip()
    if not notes:
        raise ReleaseNotesError(f"the exact '{heading}' section has no release notes")
    return notes + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        notes = extract(args.changelog.read_text(encoding="utf-8"), args.tag)
        args.output.write_text(notes, encoding="utf-8")
    except (OSError, ReleaseNotesError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"release notes extracted for {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
