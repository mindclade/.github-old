#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

"""Small dependency-free GitHub REST client for estate automation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


class GitHubAPIError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None) -> None:
        self.token = (token or os.environ.get("GH_TOKEN", "")).strip()
        self.api_url = (api_url or os.environ.get("GITHUB_API_URL", "https://api.github.com")).rstrip("/")
        if not self.token:
            raise GitHubAPIError("GH_TOKEN is required")

    def request(self, method: str, path: str, *, allow_not_found: bool = False) -> Any:
        request = urllib.request.Request(
            self.api_url + path,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "mindclade-estate-automation/1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            if allow_not_found and exc.code == 404:
                return None
            detail = exc.read().decode("utf-8", errors="replace")[:2048]
            raise GitHubAPIError(f"GitHub API {method} {path} failed: {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"GitHub API {method} {path} unavailable: {exc}") from exc
        if not payload:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise GitHubAPIError(f"GitHub API {method} {path} returned invalid JSON") from exc

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        return self.request("GET", path, allow_not_found=allow_not_found)

    def delete(self, path: str) -> None:
        self.request("DELETE", path)

    def paginate(self, path: str) -> list[Any]:
        separator = "&" if "?" in path else "?"
        result: list[Any] = []
        for page in range(1, 101):
            payload = self.get(f"{path}{separator}per_page=100&page={page}")
            if not isinstance(payload, list):
                raise GitHubAPIError(f"GitHub API pagination path did not return a list: {path}")
            result.extend(payload)
            if len(payload) < 100:
                return result
        raise GitHubAPIError(f"GitHub API pagination exceeded 100 pages: {path}")
