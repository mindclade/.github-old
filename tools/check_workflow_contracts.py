#!/usr/bin/env python3
"""Detect breaking API drift in versioned reusable GitHub workflows.

The parser is intentionally narrow and dependency-free: it reads only the stable workflow_call
surface (inputs/secrets/outputs), job IDs, and explicit permission maps. Runtime implementation
steps are free to change without rewriting the contract snapshot.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
CONTRACT_DIR = ROOT / "contracts" / "workflows"
ENTRY_RE = re.compile(r"^ {6}([A-Za-z0-9_-]+):\s*$")
ATTR_RE = re.compile(r"^ {8}(required|type|default):\s*(.*?)\s*$")
PERMISSION_RE = re.compile(r"^ +(actions|artifact-metadata|attestations|checks|contents|deployments|discussions|id-token|issues|models|packages|pages|pull-requests|repository-projects|security-events|statuses):\s*(read|write|none)\s*(?:#.*)?$")
JOB_RE = re.compile(r"^ {2}([A-Za-z0-9_-]+):\s*$")


def scalar(raw: str) -> Any:
    raw = re.sub(r"\s+#.*$", "", raw).strip()
    if raw in {"true", "false"}:
        return raw == "true"
    if re.fullmatch(r"-?[0-9]+", raw):
        return int(raw)
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        try:
            return ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            pass
    return raw


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def workflow_call_section(lines: list[str], section: str) -> dict[str, dict[str, Any]]:
    try:
        call = next(i for i, line in enumerate(lines) if line == "  workflow_call:")
    except StopIteration as exc:
        raise ValueError("missing on.workflow_call") from exc

    section_line = f"    {section}:"
    start = None
    for i in range(call + 1, len(lines)):
        if lines[i] == section_line:
            start = i + 1
            break
        if lines[i] and indent(lines[i]) <= 2:
            break
    if start is None:
        return {}

    result: dict[str, dict[str, Any]] = {}
    current: str | None = None
    for line in lines[start:]:
        if line and indent(line) <= 4:
            break
        match = ENTRY_RE.match(line)
        if match:
            current = match.group(1)
            result[current] = {}
            continue
        match = ATTR_RE.match(line)
        if match and current:
            key, value = match.groups()
            result[current][key] = scalar(value)
    return result


def permissions_at(lines: list[str], marker_index: int, marker_indent: int) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines[marker_index + 1 :]:
        if line and indent(line) <= marker_indent:
            break
        match = PERMISSION_RE.match(line)
        if match and indent(line) == marker_indent + 2:
            result[match.group(1)] = match.group(2)
    return dict(sorted(result.items()))


def extract(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if "  workflow_call:" not in lines:
        raise ValueError("not a reusable workflow")

    inputs = workflow_call_section(lines, "inputs")
    secrets = workflow_call_section(lines, "secrets")
    outputs = sorted(workflow_call_section(lines, "outputs"))

    top_permissions: dict[str, str] = {}
    jobs: list[str] = []
    job_permissions: dict[str, dict[str, str]] = {}

    for i, line in enumerate(lines):
        if line == "permissions:":
            top_permissions = permissions_at(lines, i, 0)
            break

    try:
        jobs_index = lines.index("jobs:")
    except ValueError as exc:
        raise ValueError("missing jobs mapping") from exc

    job_starts: list[tuple[str, int]] = []
    for i in range(jobs_index + 1, len(lines)):
        match = JOB_RE.match(lines[i])
        if match:
            job_starts.append((match.group(1), i))
    jobs = [name for name, _ in job_starts]

    for pos, (job, start) in enumerate(job_starts):
        end = job_starts[pos + 1][1] if pos + 1 < len(job_starts) else len(lines)
        for i in range(start + 1, end):
            if lines[i] == "    permissions:":
                job_permissions[job] = permissions_at(lines, i, 4)
                break

    return {
        "schema_version": 1,
        "workflow": path.relative_to(ROOT).as_posix(),
        "inputs": dict(sorted(inputs.items())),
        "secrets": dict(sorted(secrets.items())),
        "outputs": outputs,
        "jobs": jobs,
        "permissions": top_permissions,
        "job_permissions": dict(sorted(job_permissions.items())),
    }


def contract_path(workflow: Path) -> Path:
    return CONTRACT_DIR / f"{workflow.stem}.json"


def render(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def reusable_workflows() -> list[Path]:
    return sorted(WORKFLOW_DIR.glob("reusable-*.yml"))


def update() -> int:
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    expected = {contract_path(path) for path in reusable_workflows()}
    for stale in CONTRACT_DIR.glob("reusable-*.json"):
        if stale not in expected:
            stale.unlink()
    for workflow in reusable_workflows():
        contract_path(workflow).write_text(render(extract(workflow)), encoding="utf-8")
    print(f"updated {len(expected)} workflow contract snapshot(s)")
    return 0


def check() -> int:
    errors = 0
    workflows = reusable_workflows()
    expected_contracts = {contract_path(path) for path in workflows}
    actual_contracts = set(CONTRACT_DIR.glob("reusable-*.json"))

    for stale in sorted(actual_contracts - expected_contracts):
        print(f"orphan workflow contract: {stale.relative_to(ROOT)}", file=sys.stderr)
        errors += 1

    for workflow in workflows:
        snapshot = contract_path(workflow)
        if not snapshot.is_file():
            print(f"missing workflow contract: {snapshot.relative_to(ROOT)}", file=sys.stderr)
            errors += 1
            continue
        actual = render(extract(workflow))
        expected = snapshot.read_text(encoding="utf-8")
        if actual == expected:
            continue
        errors += 1
        print(f"workflow contract drift: {workflow.relative_to(ROOT)}", file=sys.stderr)
        diff = difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=str(snapshot.relative_to(ROOT)),
            tofile=str(workflow.relative_to(ROOT)),
            lineterm="",
        )
        for line in diff:
            print(line, file=sys.stderr)

    if errors:
        print(
            "contract check failed; breaking changes require an intentional major-version "
            "decision and refreshed snapshots with --update",
            file=sys.stderr,
        )
        return 1
    print(f"workflow contracts passed: {len(workflows)} reusable workflow(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="rewrite snapshots from current workflows")
    args = parser.parse_args()
    return update() if args.update else check()


if __name__ == "__main__":
    raise SystemExit(main())
