#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Build a deterministic seven-repository GitHub estate dashboard."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from github_api import GitHubClient

REPOSITORIES = [
    ".github",
    ".github-private",
    "bootstrap",
    "github-config",
    "gitops",
    "infrastructure-live",
    "mindclade-internal-monorepo",
]
FAILING_CONCLUSIONS = {"action_required", "cancelled", "failure", "stale", "startup_failure", "timed_out"}


def check_summary(client: GitHubClient, slug: str, commit: str) -> dict[str, int]:
    payload = client.get(f"/repos/{slug}/commits/{commit}/check-runs?per_page=100")
    runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    summary = {"total": len(runs), "pending": 0, "failing": 0}
    for run in runs:
        if run.get("status") != "completed":
            summary["pending"] += 1
        elif run.get("conclusion") in FAILING_CONCLUSIONS:
            summary["failing"] += 1
    return summary


def collect(client: GitHubClient, organization: str, repositories: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for repository in sorted(repositories):
        slug = f"{organization}/{repository}"
        metadata = client.get(f"/repos/{slug}")
        default_branch = metadata["default_branch"]
        branch = client.get(f"/repos/{slug}/branches/{default_branch}")
        default_sha = branch["commit"]["sha"]
        pulls = client.paginate(f"/repos/{slug}/pulls?state=open")
        refs = client.paginate(f"/repos/{slug}/git/matching-refs/heads/")
        tags = client.paginate(f"/repos/{slug}/git/matching-refs/tags/")
        runs_payload = client.get(f"/repos/{slug}/actions/runs?branch={default_branch}&per_page=20")
        runs = runs_payload.get("workflow_runs", []) if isinstance(runs_payload, dict) else []
        latest = runs[0] if runs else {}
        checks = check_summary(client, slug, default_sha)
        status = "green"
        if metadata.get("archived") or checks["failing"] or latest.get("conclusion") in FAILING_CONCLUSIONS:
            status = "red"
        elif checks["pending"] or not runs:
            status = "pending"
        rows.append(
            {
                "repository": repository,
                "status": status,
                "default_branch": default_branch,
                "default_sha": default_sha,
                "checks": checks,
                "latest_workflow": {
                    "name": latest.get("name", ""),
                    "status": latest.get("status", "missing"),
                    "conclusion": latest.get("conclusion"),
                    "url": latest.get("html_url", ""),
                },
                "open_pull_requests": len(pulls),
                "draft_pull_requests": sum(bool(pull.get("draft")) for pull in pulls),
                "remote_branches": max(0, len(refs) - 1),
                "tags": len(tags),
                "archived": bool(metadata.get("archived")),
            }
        )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "organization": organization,
        "repositories": rows,
        "summary": {
            "green": sum(row["status"] == "green" for row in rows),
            "pending": sum(row["status"] == "pending" for row in rows),
            "red": sum(row["status"] == "red" for row in rows),
            "open_pull_requests": sum(row["open_pull_requests"] for row in rows),
            "extra_remote_branches": sum(row["remote_branches"] for row in rows),
            "tags": sum(row["tags"] for row in rows),
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Mindclade GitHub Estate Status",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "| Repository | Status | Main checks | Latest workflow | Open PRs | Extra branches | Tags |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in report["repositories"]:
        checks = row["checks"]
        workflow = row["latest_workflow"]
        workflow_state = workflow["conclusion"] or workflow["status"]
        lines.append(
            f"| `{row['repository']}` | **{row['status']}** | {checks['total']} total / {checks['pending']} pending / {checks['failing']} failing | "
            f"{workflow['name'] or 'missing'}: {workflow_state} | {row['open_pull_requests']} | {row['remote_branches']} | {row['tags']} |"
        )
    summary = report["summary"]
    lines.extend(
        [
            "",
            f"Summary: **{summary['green']} green**, **{summary['pending']} pending**, **{summary['red']} red**; "
            f"{summary['open_pull_requests']} open PRs, {summary['extra_remote_branches']} extra branches, {summary['tags']} tags.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--organization", default="mindclade")
    parser.add_argument("--repositories", default=",".join(REPOSITORIES))
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    repositories = [value.strip() for value in args.repositories.split(",") if value.strip()]
    if sorted(repositories) != sorted(REPOSITORIES):
        parser.error("--repositories must name the exact seven-repository estate")
    report = collect(GitHubClient(), args.organization, repositories)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(markdown(report))
    return 1 if report["summary"]["red"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
