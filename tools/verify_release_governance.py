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
EXPECTED_CREATION_RULESET = "release-tag-creation"
EXPECTED_PROTECTION_RULESET = "tag-protection"
EXPECTED_TAG_PATTERN = r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


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


def validate_environment(payload: Any, expected_name: str, expected_team: str) -> int:
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
    reviewers = sequence(reviewer_rule.get("reviewers"), f"{expected_name}.reviewers")
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
        if isinstance(rule, dict) and rule.get("name") == EXPECTED_CREATION_RULESET
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
        ("name", EXPECTED_CREATION_RULESET),
        ("enforcement", "active"),
        ("target", "tag"),
        ("source_type", "Organization"),
    ):
        if ruleset.get(field) != expected:
            raise GovernanceError(f"release-tag-creation {field} must equal {expected}")

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


def validate_tag_protection_ruleset(summaries: Any, detail: Any) -> None:
    rulesets = sequence(summaries, "rulesets")
    candidates = [
        mapping(rule, "ruleset summary")
        for rule in rulesets
        if isinstance(rule, dict) and rule.get("name") == EXPECTED_PROTECTION_RULESET
    ]
    if len(candidates) != 1:
        raise GovernanceError(
            "tag-protection must be present exactly once in effective rulesets"
        )
    summary = candidates[0]
    for field, expected in (
        ("enforcement", "active"),
        ("target", "tag"),
        ("source_type", "Organization"),
    ):
        if summary.get(field) != expected:
            raise GovernanceError(
                f"tag-protection summary {field} must equal {expected}"
            )
    ruleset_id = positive_id(summary.get("id"), "tag-protection.id")

    ruleset = mapping(detail, "tag-protection")
    for field, expected in (
        ("id", ruleset_id),
        ("name", EXPECTED_PROTECTION_RULESET),
        ("enforcement", "active"),
        ("target", "tag"),
        ("source_type", "Organization"),
    ):
        if ruleset.get(field) != expected:
            raise GovernanceError(f"tag-protection {field} must equal {expected}")
    if ruleset.get("conditions") != {
        "ref_name": {"exclude": [], "include": ["refs/tags/v*"]}
    }:
        raise GovernanceError("tag-protection must target exactly refs/tags/v*")
    if ruleset.get("bypass_actors") != []:
        raise GovernanceError("tag-protection must have no bypass actors")

    rules = sequence(ruleset.get("rules"), "tag-protection.rules")
    by_type: dict[str, list[dict[str, Any]]] = {}
    for index, raw_rule in enumerate(rules):
        rule = mapping(raw_rule, f"tag-protection.rules[{index}]")
        rule_type = rule.get("type")
        if not isinstance(rule_type, str):
            raise GovernanceError("tag-protection rule type is absent")
        by_type.setdefault(rule_type, []).append(rule)
    expected_types = {"deletion", "non_fast_forward", "tag_name_pattern", "update"}
    if set(by_type) != expected_types or any(
        len(found) != 1 for found in by_type.values()
    ):
        raise GovernanceError(
            "tag-protection must contain the exact four immutability rules"
        )
    for rule_type in ("deletion", "non_fast_forward", "update"):
        if by_type[rule_type][0] != {"type": rule_type}:
            raise GovernanceError(
                f"tag-protection {rule_type} rule must have no parameters"
            )
    if by_type["tag_name_pattern"][0] != {
        "type": "tag_name_pattern",
        "parameters": {
            "name": "stable-semver-only",
            "negate": False,
            "operator": "regex",
            "pattern": EXPECTED_TAG_PATTERN,
        },
    }:
        raise GovernanceError(
            "tag-protection must require the exact stable SemVer pattern"
        )


def validate_immutable_releases(payload: Any) -> None:
    settings = mapping(payload, "immutable releases")
    if settings.get("enabled") is not True:
        raise GovernanceError("immutable releases must be enabled")
    if settings.get("enforced_by_owner") is not True:
        raise GovernanceError(
            "immutable releases must be enforced by the organization owner"
        )


def validate_approval_history(
    payload: Any, dispatcher: str
) -> dict[str, dict[str, Any]]:
    if not LOGIN.fullmatch(dispatcher):
        raise GovernanceError("workflow dispatcher login is invalid")
    reviews = sequence(payload, "workflow approval history")
    by_environment: dict[str, list[dict[str, Any]]] = {
        name: [] for name in EXPECTED_ENVIRONMENTS
    }
    for index, raw_review in enumerate(reviews):
        review = mapping(raw_review, f"workflow approval history[{index}]")
        environments = sequence(
            review.get("environments"),
            f"workflow approval history[{index}].environments",
        )
        names = [
            mapping(item, "approval environment").get("name") for item in environments
        ]
        relevant = [name for name in names if name in EXPECTED_ENVIRONMENTS]
        if not relevant:
            continue
        if review.get("state") != "approved":
            raise GovernanceError(
                "release environment review history contains a non-approval"
            )
        user = mapping(review.get("user"), "workflow approval reviewer")
        login = user.get("login")
        if not isinstance(login, str) or not LOGIN.fullmatch(login):
            raise GovernanceError("workflow approval reviewer login is invalid")
        reviewer_id = positive_id(user.get("id"), "workflow approval reviewer.id")
        if login.casefold() == dispatcher.casefold():
            raise GovernanceError(
                "workflow dispatcher cannot approve a release environment"
            )
        reviewer = {"id": reviewer_id, "login": login}
        for name in relevant:
            by_environment[name].append(reviewer)
    if any(len(reviewers) != 1 for reviewers in by_environment.values()):
        raise GovernanceError(
            "each release environment requires exactly one approved review"
        )
    approved = {name: reviewers[0] for name, reviewers in by_environment.items()}
    if len({reviewer["id"] for reviewer in approved.values()}) != len(approved):
        raise GovernanceError("release environments require distinct human reviewers")
    return approved


def validate_team_membership(payload: Any, team: str, login: str) -> None:
    membership = mapping(payload, f"{team} membership for {login}")
    if membership.get("state") != "active" or membership.get("role") not in {
        "member",
        "maintainer",
    }:
        raise GovernanceError(f"{login} must be an active member of the {team} team")


def validate_snapshot(
    environments: dict[str, Any],
    rulesets: Any,
    creation_ruleset: Any,
    protection_ruleset: Any,
    expected_release_team_id: int,
) -> None:
    reviewer_ids = {
        name: validate_environment(environments.get(name), name, team)
        for name, team in EXPECTED_ENVIRONMENTS.items()
    }
    if len(set(reviewer_ids.values())) != len(reviewer_ids):
        raise GovernanceError("release environments must use distinct reviewer teams")
    validate_release_ruleset(rulesets, creation_ruleset, expected_release_team_id)
    validate_tag_protection_ruleset(rulesets, protection_ruleset)


class GitHubClient:
    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
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
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "mindclade-release-governance-preflight",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response), dict(response.headers.items())
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            json.JSONDecodeError,
        ) as error:
            status = getattr(error, "code", "unavailable")
            raise GovernanceError(
                f"GitHub API read failed for {path}: {status}"
            ) from error

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
    client: GitHubClient,
    repository: str,
    expected_release_team_id: int,
    *,
    run_id: int | None = None,
    dispatcher: str | None = None,
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
    details: dict[str, Any] = {}
    for name in (EXPECTED_CREATION_RULESET, EXPECTED_PROTECTION_RULESET):
        candidates = [rule for rule in summaries if rule.get("name") == name]
        if len(candidates) != 1:
            raise GovernanceError(
                f"{name} must be present exactly once in effective rulesets"
            )
        ruleset_id = positive_id(candidates[0].get("id"), f"{name}.id")
        details[name] = client.get(f"/repos/{repository}/rulesets/{ruleset_id}")[0]
    validate_snapshot(
        environments,
        summaries,
        details[EXPECTED_CREATION_RULESET],
        details[EXPECTED_PROTECTION_RULESET],
        expected_release_team_id,
    )
    immutable_releases = client.get(f"/repos/{repository}/immutable-releases")[0]
    validate_immutable_releases(immutable_releases)
    if (run_id is None) != (dispatcher is None):
        raise GovernanceError(
            "workflow run ID and dispatcher must be provided together"
        )
    if run_id is not None and dispatcher is not None:
        approvals = client.get(f"/repos/{repository}/actions/runs/{run_id}/approvals")[
            0
        ]
        approved = validate_approval_history(approvals, dispatcher)
        organization = repository.split("/", 1)[0]
        for environment, reviewer in approved.items():
            team = EXPECTED_ENVIRONMENTS[environment]
            membership = client.get(
                f"/orgs/{organization}/teams/{team}/memberships/{reviewer['login']}"
            )[0]
            validate_team_membership(membership, team, reviewer["login"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--release-team-id", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--dispatcher")
    parser.add_argument(
        "--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com")
    )
    args = parser.parse_args()
    try:
        release_team_id = positive_id(args.release_team_id, "release team ID")
        token = os.environ.get("GH_TOKEN", "")
        if not token:
            raise GovernanceError(
                "GH_TOKEN is required for connected read-only qualification"
            )
        verify_connected(
            GitHubClient(token=token, api_url=args.api_url),
            args.repository,
            release_team_id,
            run_id=positive_id(args.run_id, "workflow run ID") if args.run_id else None,
            dispatcher=args.dispatcher,
        )
    except GovernanceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("connected release governance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
