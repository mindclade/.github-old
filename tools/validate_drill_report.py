#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Fail-closed semantic validation for Mindclade DR report v2 JSON."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

DRILLS = {"bootstrap-clean-room", "terraform-state-recovery", "github-idp-outage", "org-policy-rollback", "vpc-sc-lockout", "gke-reconstruction", "argocd-rebootstrap", "cloud-sql-restore", "protected-bucket-restore", "compromised-artifact-revocation"}
REQUIRED = {"schema_version", "drill_id", "drill_type", "scope", "environment", "operators", "source_revisions", "started_at", "ended_at", "result", "objectives", "recovery_point", "recovery_time_seconds", "success_criteria", "abort_conditions", "evidence", "failures", "corrective_actions", "next_drill_at"}
ALLOWED = REQUIRED | {"commands"}
RE_DRILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,79}$")
RE_IDENTITY = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
RE_SHA = re.compile(r"^[0-9a-f]{40}$")
RE_SHA256 = re.compile(r"^[0-9a-f]{64}$")
RE_EVIDENCE = re.compile(r"^(?:gs://|https://github[.]com/).+")


def timestamp(value: Any, name: str, errors: list[str]) -> dt.datetime | None:
    if not isinstance(value, str):
        errors.append(f"{name} must be an RFC 3339 timestamp")
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{name} must be an RFC 3339 timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{name} must include a UTC offset")
        return None
    return parsed


def mapping(value: Any, name: str, required: set[str], errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return None
    errors.extend(f"missing: {name}.{key}" for key in sorted(required - value.keys()))
    errors.extend(f"unknown: {name}.{key}" for key in sorted(value.keys() - required))
    return value


def integer(value: Any, name: str, errors: list[str], minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        errors.append(f"{name} must be an integer >= {minimum}")


def string_array(value: Any, name: str, errors: list[str], minimum: int = 0) -> None:
    if not isinstance(value, list) or len(value) < minimum:
        errors.append(f"{name} must contain at least {minimum} item(s)")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{name}[{index}] must be a non-empty string")


def validate(report: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    errors.extend(f"missing: {key}" for key in sorted(REQUIRED - report.keys()))
    errors.extend(f"unknown: {key}" for key in sorted(report.keys() - ALLOWED))
    if report.get("schema_version") != 2:
        errors.append("schema_version must equal 2")
    if not isinstance(report.get("drill_id"), str) or not RE_DRILL_ID.fullmatch(report["drill_id"]):
        errors.append("drill_id is invalid")
    if report.get("drill_type") not in DRILLS:
        errors.append("drill_type is not supported")
    if not isinstance(report.get("scope"), str) or not report["scope"].strip():
        errors.append("scope must be a non-empty string")
    if report.get("environment") not in {"scratch", "staging"}:
        errors.append("environment must be scratch or staging")
    if report.get("result") not in {"pass", "partial", "fail"}:
        errors.append("result must be pass, partial, or fail")

    operators = report.get("operators")
    identities: list[str] = []
    roles: list[str] = []
    if not isinstance(operators, list) or len(operators) < 2:
        errors.append("operators must contain at least two entries")
    else:
        for index, item in enumerate(operators):
            operator = mapping(item, f"operators[{index}]", {"identity", "role"}, errors)
            if not operator:
                continue
            identity, role = operator.get("identity"), operator.get("role")
            if not isinstance(identity, str) or not RE_IDENTITY.fullmatch(identity):
                errors.append(f"operators[{index}].identity is invalid")
            else:
                identities.append(identity)
            if role not in {"primary", "observer", "incident-commander", "service-owner"}:
                errors.append(f"operators[{index}].role is invalid")
            else:
                roles.append(role)
        if len(identities) != len(set(identities)):
            errors.append("operator identities must be distinct")
        if "primary" not in roles or "observer" not in roles:
            errors.append("operators must include primary and observer roles")

    revisions = report.get("source_revisions")
    if not isinstance(revisions, dict) or not revisions:
        errors.append("source_revisions must be a non-empty object")
    else:
        for name, revision in revisions.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(revision, str) or not RE_SHA.fullmatch(revision):
                errors.append(f"source_revisions.{name} is invalid")

    started = timestamp(report.get("started_at"), "started_at", errors)
    ended = timestamp(report.get("ended_at"), "ended_at", errors)
    next_drill = timestamp(report.get("next_drill_at"), "next_drill_at", errors)
    if started and ended and ended < started:
        errors.append("ended_at precedes started_at")
    if ended and next_drill and next_drill <= ended:
        errors.append("next_drill_at must follow ended_at")

    objectives = mapping(report.get("objectives"), "objectives", {"rpo_seconds", "rto_seconds"}, errors)
    if objectives:
        integer(objectives.get("rpo_seconds"), "objectives.rpo_seconds", errors)
        integer(objectives.get("rto_seconds"), "objectives.rto_seconds", errors, 1)
    recovery = mapping(report.get("recovery_point"), "recovery_point", {"description", "observed_at", "rpo_seconds"}, errors)
    if recovery:
        if not isinstance(recovery.get("description"), str) or not recovery["description"].strip():
            errors.append("recovery_point.description must be a non-empty string")
        timestamp(recovery.get("observed_at"), "recovery_point.observed_at", errors)
        integer(recovery.get("rpo_seconds"), "recovery_point.rpo_seconds", errors)
    integer(report.get("recovery_time_seconds"), "recovery_time_seconds", errors)
    string_array(report.get("success_criteria"), "success_criteria", errors, 1)
    string_array(report.get("abort_conditions"), "abort_conditions", errors, 1)
    string_array(report.get("failures"), "failures", errors)
    if "commands" in report:
        string_array(report.get("commands"), "commands", errors)

    evidence = report.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must contain at least one entry")
    else:
        for index, item in enumerate(evidence):
            entry = mapping(item, f"evidence[{index}]", {"uri", "sha256", "classification"}, errors)
            if not entry:
                continue
            if not isinstance(entry.get("uri"), str) or not RE_EVIDENCE.fullmatch(entry["uri"]):
                errors.append(f"evidence[{index}].uri is invalid")
            if not isinstance(entry.get("sha256"), str) or not RE_SHA256.fullmatch(entry["sha256"]):
                errors.append(f"evidence[{index}].sha256 is invalid")
            if entry.get("classification") not in {"internal", "confidential", "restricted"}:
                errors.append(f"evidence[{index}].classification is invalid")

    actions, open_actions = report.get("corrective_actions"), 0
    if not isinstance(actions, list):
        errors.append("corrective_actions must be a list")
    else:
        for index, item in enumerate(actions):
            action = mapping(item, f"corrective_actions[{index}]", {"owner", "action", "due_at", "status"}, errors)
            if not action:
                continue
            for field in ("owner", "action"):
                if not isinstance(action.get(field), str) or not action[field].strip():
                    errors.append(f"corrective_actions[{index}].{field} is invalid")
            timestamp(action.get("due_at"), f"corrective_actions[{index}].due_at", errors)
            if action.get("status") not in {"open", "complete"}:
                errors.append(f"corrective_actions[{index}].status is invalid")
            elif action["status"] == "open":
                open_actions += 1

    result, failures = report.get("result"), report.get("failures")
    if result == "pass":
        if isinstance(failures, list) and failures:
            errors.append("a passing drill cannot contain failures")
        if open_actions:
            errors.append("a passing drill cannot contain open corrective actions")
        if objectives and recovery:
            if isinstance(recovery.get("rpo_seconds"), int) and isinstance(objectives.get("rpo_seconds"), int) and recovery["rpo_seconds"] > objectives["rpo_seconds"]:
                errors.append("observed RPO exceeds the objective")
            if isinstance(report.get("recovery_time_seconds"), int) and isinstance(objectives.get("rto_seconds"), int) and report["recovery_time_seconds"] > objectives["rto_seconds"]:
                errors.append("observed RTO exceeds the objective")
    elif result in {"partial", "fail"}:
        if not isinstance(failures, list) or not failures:
            errors.append("a partial or failed drill must record a failure")
        if not open_actions:
            errors.append("a partial or failed drill must have an open corrective action")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"unable to read report: {exc}"]
    print(json.dumps({"schema_version": 2, "status": "FAIL" if errors else "PASS", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
