#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Plan or execute conservative cleanup of merged branches and unauthorized tags."""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from github_api import GitHubClient


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def object_details(client: GitHubClient, slug: str, object_type: str, sha: str) -> tuple[datetime, str | None]:
    observed_at: datetime | None = None
    for _ in range(5):
        if object_type == "commit":
            commit = client.get(f"/repos/{slug}/commits/{sha}")
            return observed_at or parse_time(commit["commit"]["committer"]["date"]), sha
        if object_type != "tag":
            break
        tag = client.get(f"/repos/{slug}/git/tags/{sha}")
        observed_at = observed_at or parse_time(tag["tagger"]["date"])
        target = tag.get("object", {})
        object_type, sha = target.get("type", ""), target.get("sha", "")
    return observed_at or datetime.max.replace(tzinfo=timezone.utc), None


def comparison(client: GitHubClient, slug: str, default_branch: str, reference: str) -> dict[str, Any]:
    return client.get(
        f"/repos/{slug}/compare/{urllib.parse.quote(default_branch, safe='')}..."
        f"{urllib.parse.quote(reference, safe='')}"
    )


def repository_plan(client: GitHubClient, organization: str, repository: str, policy: dict[str, Any], now: datetime) -> dict[str, Any]:
    slug = f"{organization}/{repository}"
    metadata = client.get(f"/repos/{slug}")
    default_branch = metadata["default_branch"]
    open_pulls = client.paginate(f"/repos/{slug}/pulls?state=open")
    pull_branches = {pull.get("head", {}).get("ref") for pull in open_pulls}
    branch_refs = client.paginate(f"/repos/{slug}/git/matching-refs/heads/")
    tag_refs = client.paginate(f"/repos/{slug}/git/matching-refs/tags/")
    protected = set(policy["protected_branches"]) | {default_branch}
    protected_prefixes = tuple(policy["protected_branch_prefixes"])
    branch_cutoff = now - timedelta(days=policy["branch_retention_days"])
    tag_cutoff = now - timedelta(days=policy["tag_retention_days"])
    allowed_tags = [re.compile(pattern) for pattern in policy["allowed_tag_patterns"]]
    branches: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []

    for reference in branch_refs:
        branch = reference["ref"].removeprefix("refs/heads/")
        sha = reference["object"]["sha"]
        decision = "preserve"
        reason = "protected"
        if branch not in protected and not branch.startswith(protected_prefixes) and branch not in pull_branches:
            branch_comparison = comparison(client, slug, default_branch, branch)
            updated_at, _ = object_details(client, slug, reference["object"]["type"], sha)
            if branch_comparison.get("ahead_by") == 0 and updated_at <= branch_cutoff:
                decision, reason = "delete", "merged_and_retained"
            elif branch_comparison.get("ahead_by") == 0:
                reason = "merged_within_retention"
            else:
                reason = "contains_unique_commits"
        elif branch in pull_branches:
            reason = "open_pull_request"
        branches.append({"name": branch, "sha": sha, "decision": decision, "reason": reason})

    for reference in tag_refs:
        tag_name = reference["ref"].removeprefix("refs/tags/")
        sha = reference["object"]["sha"]
        decision = "preserve"
        reason = "allowed_pattern"
        if not any(pattern.fullmatch(tag_name) for pattern in allowed_tags):
            release = client.get(f"/repos/{slug}/releases/tags/{urllib.parse.quote(tag_name, safe='')}", allow_not_found=True)
            created_at, commit_sha = object_details(client, slug, reference["object"]["type"], sha)
            if release is not None:
                reason = "published_release"
            elif commit_sha is None:
                reason = "unsupported_target"
            elif comparison(client, slug, default_branch, commit_sha).get("ahead_by") != 0:
                reason = "contains_unique_commits"
            elif created_at <= tag_cutoff:
                decision, reason = "delete", "unauthorized_and_retained"
            else:
                reason = "unauthorized_within_retention"
        tags.append({"name": tag_name, "sha": sha, "decision": decision, "reason": reason})
    return {"repository": repository, "default_branch": default_branch, "branches": branches, "tags": tags}


def plan(client: GitHubClient, config: dict[str, Any], now: Any = None) -> dict[str, Any]:
    if config.get("schema_version") != 1 or config.get("organization") != "mindclade":
        raise ValueError("maintenance config identity is invalid")
    repositories = config.get("repositories")
    if not isinstance(repositories, dict) or not repositories:
        raise ValueError("maintenance config has no repositories")
    observed_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    rows = [
        repository_plan(client, config["organization"], repository, policy, observed_at)
        for repository, policy in sorted(repositories.items())
    ]
    return {
        "schema_version": 1,
        "generated_at": observed_at.isoformat().replace("+00:00", "Z"),
        "organization": config["organization"],
        "repositories": rows,
        "summary": {
            "branch_deletions": sum(item["decision"] == "delete" for row in rows for item in row["branches"]),
            "tag_deletions": sum(item["decision"] == "delete" for row in rows for item in row["tags"]),
        },
    }


def ensure_candidate(client: GitHubClient, slug: str, default_branch: str, kind: str, item: dict[str, Any]) -> str:
    namespace = "heads" if kind == "branches" else "tags"
    encoded = urllib.parse.quote(item["name"], safe="")
    path = f"/repos/{slug}/git/ref/{namespace}/{encoded}"
    current = client.get(path)
    if current.get("object", {}).get("sha") != item["sha"]:
        raise ValueError(f"ref moved after planning: {slug}:{namespace}/{item['name']}")
    if kind == "branches":
        pulls = client.paginate(f"/repos/{slug}/pulls?state=open")
        if item["name"] in {pull.get("head", {}).get("ref") for pull in pulls}:
            raise ValueError(f"branch gained an open pull request: {slug}:{item['name']}")
        if comparison(client, slug, default_branch, item["name"]).get("ahead_by") != 0:
            raise ValueError(f"branch gained unique commits: {slug}:{item['name']}")
    else:
        release = client.get(
            f"/repos/{slug}/releases/tags/{urllib.parse.quote(item['name'], safe='')}",
            allow_not_found=True,
        )
        if release is not None:
            raise ValueError(f"tag became a published release: {slug}:{item['name']}")
    return f"/repos/{slug}/git/refs/{namespace}/{encoded}"


def execute(client: GitHubClient, report: dict[str, Any]) -> None:
    if report.get("schema_version") != 1 or report.get("organization") != "mindclade":
        raise ValueError("maintenance report identity is invalid")
    organization = report["organization"]
    candidates: list[tuple[str, str, str, dict[str, Any]]] = []
    for row in report["repositories"]:
        slug = f"{organization}/{row['repository']}"
        for kind in ("branches", "tags"):
            for item in row[kind]:
                if item["decision"] != "delete":
                    continue
                ensure_candidate(client, slug, row["default_branch"], kind, item)
                candidates.append((slug, row["default_branch"], kind, item))
    for slug, default_branch, kind, item in candidates:
        client.delete(ensure_candidate(client, slug, default_branch, kind, item))


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Mindclade Ref Janitor", "", f"Generated: `{report['generated_at']}`", ""]
    for row in report["repositories"]:
        lines.extend([f"## {row['repository']}", "", "| Ref | Decision | Reason |", "|---|---|---|"])
        for kind in ("branches", "tags"):
            label = "branch" if kind == "branches" else "tag"
            for item in row[kind]:
                lines.append(f"| `{label}:{item['name']}` | **{item['decision']}** | {item['reason']} |")
        lines.append("")
    lines.append(
        f"Candidates: **{report['summary']['branch_deletions']} branches**, **{report['summary']['tag_deletions']} tags**."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--mode", choices=("report", "delete"), default="report")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    client = GitHubClient()
    report = plan(client, config)
    if args.mode == "delete":
        if args.confirmation != "DELETE":
            parser.error("--confirmation DELETE is required for deletion")
        execute(client, report)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
