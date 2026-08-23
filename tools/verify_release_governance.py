#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary
"""Fail closed unless connected GitHub release governance is exact."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


EXPECTED_ENVIRONMENTS = {
    "workflow-release-platform": "platform",
    "workflow-release-security": "security",
}
EXPECTED_RULESET = "release-tag-creation"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class GovernanceError(ValueError):
    """Connected governance is absent, inaccessible, or unsafe."""


def mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GovernanceError(f"{label} must be one JSON object")
    return value


def sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GovernanceError(f"{label} must be one JSON array")
    return value


def positive_id(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise GovernanceError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise GovernanceError(f"{label} must be a positive integer") from error
    if result <= 0 or str(value) != str(result):
        raise GovernanceError(f"{label} must be a positive integer")
    return result


def validate_environment(
    payload: Any, expected_name: str, expected_team: str
) -> int:
    environment = mapping(payload, expected_name)
    if environment.get("name") != expected_name:
        raise GovernanceError(f"{expected_name}: environment name differs")
    if environment.get("can_admins_bypass") is not False:
        raise GovernanceError(f"{expected_name}: administrator bypass must be disabled")

    branch_policy = mapping(
        environment.get("deployment_branch_policy"),
        f"{expected_name}.deployment_branch_policy",
    )
    expected_branch_policy = {
        "protected_branches": True,
        "custom_branch_policies": False,
    }
    if branch_policy != expected_branch_policy:
        raise GovernanceError(
            f"{expected_name}: deployment must be protected-branches-only"
        )

    rules = sequence(environment.get("protection_rules"), f"{expected_name}.rules")
    by_type: dict[str, list[dict[str, Any]]] = {}
    for index, raw_rule in enumerate(rules):
        rule = mapping(raw_rule, f"{expected_name}.rules[{index}]")
        rule_type = rule.get("type")
        if not isinstance(rule_type, str):
            raise GovernanceError(f"{expected_name}: protection rule type is absent")
        by_type.setdefault(rule_type, []).append(rule)
    if set(by_type) != {"branch_policy", "required_reviewers"} or any(
        len(found) != 1 for found in by_type.values()
    ):
        raise GovernanceError(
            f"{expected_name}: protection rules must be exactly branch policy and reviewers"
        )

    reviewer_rule = by_type["required_reviewers"][0]
    if reviewer_rule.get("prevent_self_review") is not True:
        raise GovernanceError(f"{expected_name}: self-review must be disabled")
    reviewers = sequence(
        reviewer_rule.get("reviewers"), f"{expected_name}.reviewers"
    )
    if len(reviewers) != 1:
        raise GovernanceError(f"{expected_name}: exactly one reviewer team is required")
    entry = mapping(reviewers[0], f"{expected_name}.reviewers[0]")
    if entry.get("type") != "Team":
        raise GovernanceError(f"{expected_name}: reviewer must be a team")
    reviewer = mapping(entry.get("reviewer"), f"{expected_name}.reviewer")
    if reviewer.get("slug") != expected_team:
        raise GovernanceError(
            f"{expected_name}: reviewer must be the {expected_team} team"
        )
    return positive_id(reviewer.get("id"), f"{expected_name}.reviewer.id")


def validate_release_ruleset(
    summaries: Any, detail: Any, expected_release_team_id: int
) -> None:
    rulesets = sequence(summaries, "rulesets")
    candidates = [
        mapping(rule, "ruleset summary")
        for rule in rulesets
        if isinstance(rule, dict) and rule.get("name") == EXPECTED_RULESET
    ]
    if len(candidates) != 1:
        raise GovernanceError(
            "release-tag-creation must be present exactly once in effective rulesets"
        )
    summary = candidates[0]
    for field, expected in (
        ("enforcement", "active"),
        ("target", "tag"),
        ("source_type", "Organization"),
    ):
        if summary.get(field) != expected:
            raise GovernanceError(
                f"release-tag-creation summary {field} must equal {expected}"
            )
    ruleset_id = positive_id(summary.get("id"), "release-tag-creation.id")

    ruleset = mapping(detail, "release-tag-creation")
    for field, expected in (
        ("id", ruleset_id),
        ("name", EXPECTED_RULESET),
        ("enforcement", "active"),
        ("target", "tag"),
        ("source_type", "Organization"),
    ):
        if ruleset.get(field) != expected:
            raise GovernanceError(
                f"release-tag-creation {field} must equal {expected}"
            )

    conditions = mapping(ruleset.get("conditions"), "release-tag-creation.conditions")
    if conditions != {"ref_name": {"exclude": [], "include": ["refs/tags/v*"]}}:
        raise GovernanceError(
            "release-tag-creation must target exactly refs/tags/v* for this repository"
        )
    if ruleset.get("rules") != [{"type": "creation"}]:
        raise GovernanceError(
            "release-tag-creation must contain only the tag creation restriction"
        )
    expected_bypass = [
        {
            "actor_id": expected_release_team_id,
            "actor_type": "Team",
            "bypass_mode": "always",
        }
    ]
    if ruleset.get("bypass_actors") != expected_bypass:
        raise GovernanceError(
            "release-tag-creation must have only the exact Release-team always bypass"
        )


def validate_snapshot(
    environments: dict[str, Any],
    rulesets: Any,
    ruleset: Any,
    expected_release_team_id: int,
) -> None:
    reviewer_ids = {
        name: validate_environment(environments.get(name), name, team)
        for name, team in EXPECTED_ENVIRONMENTS.items()
    }
    if len(set(reviewer_ids.values())) != len(reviewer_ids):
        raise GovernanceError("release environments must use distinct reviewer teams")
    validate_release_ruleset(rulesets, ruleset, expected_release_team_id)


class GitHubClient:
    def __init__(
        self, token: str, api_url: str = "https://api.github.com"
    ) -> None:
        self.token = token
        self.api_url = api_url

    def get(self, path: str) -> tuple[Any, dict[str, str]]:
        base = urllib.parse.urlsplit(self.api_url)
        url = urllib.parse.urljoin(self.api_url.rstrip("/") + "/", path.lstrip("/"))
        target = urllib.parse.urlsplit(url)
        if (target.scheme, target.netloc) != (base.scheme, base.netloc):
            raise GovernanceError("GitHub API pagination escaped the configured origin")
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "mindclade-release-governance-preflight",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response), dict(response.headers.items())
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as error:
            status = getattr(error, "code", "unavailable")
            raise GovernanceError(f"GitHub API read failed for {path}: {status}") from error

    def get_pages(self, path: str) -> list[Any]:
        values: list[Any] = []
        next_path: str | None = path
        while next_path is not None:
            payload, headers = self.get(next_path)
            values.extend(sequence(payload, f"GitHub API page {next_path}"))
            next_path = None
            for part in headers.get("Link", headers.get("link", "")).split(","):
                if 'rel="next"' not in part:
                    continue
                target = part.split(";", 1)[0].strip().strip("<>")
                next_path = target
                break
        return values


def verify_connected(
    client: GitHubClient, repository: str, expected_release_team_id: int
) -> None:
    if not REPOSITORY.fullmatch(repository):
        raise GovernanceError("repository must be one owner/name pair")
    environments = {
        name: client.get(f"/repos/{repository}/environments/{name}")[0]
        for name in EXPECTED_ENVIRONMENTS
    }
    summaries = client.get_pages(
        f"/repos/{repository}/rulesets?targets=tag&per_page=100"
    )
    candidates = [rule for rule in summaries if rule.get("name") == EXPECTED_RULESET]
    if len(candidates) != 1:
        raise GovernanceError(
            "release-tag-creation must be present exactly once in effective rulesets"
        )
    ruleset_id = positive_id(candidates[0].get("id"), "release-tag-creation.id")
    detail = client.get(f"/repos/{repository}/rulesets/{ruleset_id}")[0]
    validate_snapshot(environments, summaries, detail, expected_release_team_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--release-team-id", required=True)
    parser.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    args = parser.parse_args()
    try:
        release_team_id = positive_id(args.release_team_id, "release team ID")
        token = os.environ.get("GH_TOKEN", "")
        if not token:
            raise GovernanceError("GH_TOKEN is required for connected read-only qualification")
        verify_connected(
            GitHubClient(token=token, api_url=args.api_url),
            args.repository,
            release_team_id,
        )
    except GovernanceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("connected release governance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
