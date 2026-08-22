#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Detect breaking API drift in versioned reusable GitHub workflows.

The parser reads YAML semantically but projects only the stable workflow_call surface
(inputs/secrets/outputs), job IDs, and explicit permissions. Runtime implementation steps are
free to change without rewriting the contract snapshot.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode
from yaml.resolver import BaseResolver

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
CONTRACT_DIR = ROOT / "contracts" / "workflows"
ENTRY_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
CONTRACT_ATTRIBUTES = ("required", "type", "default")
PERMISSION_LEVELS = frozenset({"read", "write", "none"})
PERMISSION_SCALARS = frozenset({"read-all", "write-all"})
PERMISSION_SCOPES = frozenset(
    {
        "actions",
        "artifact-metadata",
        "attestations",
        "checks",
        "contents",
        "deployments",
        "discussions",
        "id-token",
        "issues",
        "models",
        "packages",
        "pages",
        "pull-requests",
        "repository-projects",
        "security-events",
        "statuses",
    }
)

_BOOL_TAG = "tag:yaml.org,2002:bool"
_TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"


class WorkflowLoader(yaml.SafeLoader):
    """Safe YAML loader aligned with GitHub's YAML 1.2 boolean behavior."""


WorkflowLoader.yaml_implicit_resolvers = {
    prefix: list(resolvers)
    for prefix, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for prefix, resolvers in WorkflowLoader.yaml_implicit_resolvers.items():
    WorkflowLoader.yaml_implicit_resolvers[prefix] = [
        (tag, expression)
        for tag, expression in resolvers
        if tag not in {_BOOL_TAG, _TIMESTAMP_TAG}
    ]
WorkflowLoader.add_implicit_resolver(
    _BOOL_TAG,
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _construct_unique_mapping(
    loader: WorkflowLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


WorkflowLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping)


def _mapping(value: Any, location: str) -> Mapping[Any, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{location} must be a mapping")
    return value


def _entry_name(value: Any, location: str) -> str:
    if not isinstance(value, str) or not ENTRY_NAME_RE.fullmatch(value):
        raise ValueError(f"{location} contains invalid entry name {value!r}")
    return value


def _contract_attribute(value: Any, attribute: str, location: str) -> Any:
    if attribute == "required" and not isinstance(value, bool):
        raise ValueError(f"{location}.required must be a boolean")
    if attribute == "type" and not isinstance(value, str):
        raise ValueError(f"{location}.type must be a string")
    if attribute == "default" and not (
        value is None or isinstance(value, (bool, int, float, str))
    ):
        raise ValueError(f"{location}.default must be a scalar")
    return value


def _workflow_call_section(
    workflow_call: Mapping[Any, Any], section: str
) -> dict[str, dict[str, Any]]:
    raw_section = workflow_call.get(section)
    if raw_section is None:
        return {}
    entries = _mapping(raw_section, f"on.workflow_call.{section}")
    result: dict[str, dict[str, Any]] = {}
    for raw_name, raw_attributes in entries.items():
        name = _entry_name(raw_name, f"on.workflow_call.{section}")
        attributes = (
            {}
            if raw_attributes is None
            else _mapping(raw_attributes, f"on.workflow_call.{section}.{name}")
        )
        result[name] = {
            attribute: _contract_attribute(
                attributes[attribute], attribute, f"on.workflow_call.{section}.{name}"
            )
            for attribute in CONTRACT_ATTRIBUTES
            if attribute in attributes
        }
    return dict(sorted(result.items()))


def _permissions(value: Any, location: str) -> str | dict[str, str]:
    if isinstance(value, str):
        if value not in PERMISSION_SCALARS:
            raise ValueError(
                f"{location} must be read-all, write-all, or a permission mapping"
            )
        return value
    permissions = _mapping(value, location)
    result: dict[str, str] = {}
    for raw_scope, raw_level in permissions.items():
        if not isinstance(raw_scope, str) or raw_scope not in PERMISSION_SCOPES:
            raise ValueError(f"{location} contains unknown permission scope {raw_scope!r}")
        if not isinstance(raw_level, str) or raw_level not in PERMISSION_LEVELS:
            raise ValueError(
                f"{location}.{raw_scope} must be read, write, or none"
            )
        result[raw_scope] = raw_level
    return dict(sorted(result.items()))


def _load_workflow(path: Path) -> Mapping[Any, Any]:
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=WorkflowLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid workflow YAML: {exc}") from exc
    return _mapping(document, "workflow document")


def extract(path: Path) -> dict[str, Any]:
    workflow = _load_workflow(path)
    triggers = _mapping(workflow.get("on"), "on")
    if "workflow_call" not in triggers:
        raise ValueError("missing on.workflow_call")
    raw_workflow_call = triggers["workflow_call"]
    workflow_call = (
        {} if raw_workflow_call is None else _mapping(raw_workflow_call, "on.workflow_call")
    )

    inputs = _workflow_call_section(workflow_call, "inputs")
    secrets = _workflow_call_section(workflow_call, "secrets")
    outputs = sorted(_workflow_call_section(workflow_call, "outputs"))

    top_permissions: str | dict[str, str] = {}
    if "permissions" in workflow:
        top_permissions = _permissions(workflow["permissions"], "permissions")

    raw_jobs = _mapping(workflow.get("jobs"), "jobs")
    jobs: list[str] = []
    job_permissions: dict[str, str | dict[str, str]] = {}
    for raw_job, raw_job_contract in raw_jobs.items():
        job = _entry_name(raw_job, "jobs")
        job_contract = _mapping(raw_job_contract, f"jobs.{job}")
        jobs.append(job)
        if "permissions" in job_contract:
            job_permissions[job] = _permissions(
                job_contract["permissions"], f"jobs.{job}.permissions"
            )

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
            print(
                f"missing workflow contract: {snapshot.relative_to(ROOT)}",
                file=sys.stderr,
            )
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
    parser.add_argument(
        "--update", action="store_true", help="rewrite snapshots from current workflows"
    )
    args = parser.parse_args()
    return update() if args.update else check()


if __name__ == "__main__":
    raise SystemExit(main())
