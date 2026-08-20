#!/usr/bin/env python3
"""Require immutable external action refs and controlled Mindclade workflow releases."""
from __future__ import annotations
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
errors: list[str] = []
for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
    text = path.read_text(encoding="utf-8")
    for raw in USES.findall(text):
        use = raw.strip("'\"")
        if use.startswith("./"):
            continue
        target, sep, ref = use.rpartition("@")
        if not sep:
            errors.append(f"{path.relative_to(ROOT)}: unversioned {use}")
        elif target.startswith("mindclade/.github/.github/workflows/"):
            if not SEMVER.fullmatch(ref):
                errors.append(f"{path.relative_to(ROOT)}: internal workflow must use full semver: {use}")
        elif not (SHA.fullmatch(ref) or DIGEST.fullmatch(ref)):
            errors.append(f"{path.relative_to(ROOT)}: external action must use a full SHA: {use}")
if errors:
    print("action pin validation failed:", file=sys.stderr)
    print("\n".join(f"  - {e}" for e in errors), file=sys.stderr)
    raise SystemExit(1)
print("action pin validation passed")
