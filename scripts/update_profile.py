#!/usr/bin/env python3
"""Update dynamic sections in GitHub profile README."""

from __future__ import annotations

import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USERNAME = "zakir-web3"
README_PATH = os.environ.get("README_PATH", "README.md")


def api_get(url: str) -> dict | list:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json_load(resp.read().decode())


def json_load(text: str):
    import json

    return json.loads(text)


def search_count(query: str) -> int:
    data = api_get(f"https://api.github.com/search/issues?{urllib.parse.urlencode({'q': query, 'per_page': 1})}")
    return int(data.get("total_count", 0))


def repo_stars(owner: str, repo: str) -> int:
    data = api_get(f"https://api.github.com/repos/{owner}/{repo}")
    return int(data.get("stargazers_count", 0))


def format_stars(count: int) -> str:
    return f"⭐ {count}" if count else "—"


def replace_marker(content: str, name: str, value: str) -> str:
    pattern = rf"(<!-- profile:auto:{re.escape(name)} -->)(.*?)(<!-- /profile:auto:{re.escape(name)} -->)"
    replacement = rf"\g<1>{value}\g<3>"
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"Marker profile:auto:{name} not found or duplicated")
    return updated


def main() -> int:
    merged_prs = search_count(f"repo:cosmos/cosmos-sdk author:{USERNAME} type:pr is:merged")
    bridge_stars = repo_stars(USERNAME, "bridge")
    wc_stars = repo_stars(USERNAME, "go-walletconnect-bridge")

    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    content = replace_marker(content, "cosmos-merged-prs", str(merged_prs))
    content = replace_marker(content, "bridge-stars", format_stars(bridge_stars))
    content = replace_marker(content, "wc-stars", format_stars(wc_stars))
    content = replace_marker(
        content,
        "cosmos-badge-line",
        (
            f"[![cosmos-sdk PRs](https://img.shields.io/badge/cosmos--sdk-{merged_prs}%20merged%20PRs-2E3148?style=flat-square&logo=cosmos&logoColor=white)]"
            f"(https://github.com/cosmos/cosmos-sdk/pulls?q=is%3Apr+author%3Azakir-web3+is%3Aclosed)"
        ),
    )

    with open(README_PATH, encoding="utf-8") as f:
        original = f.read()

    if content == original:
        print("Profile README already up to date.")
        return 0

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(
        "Updated profile README:",
        f"cosmos merged PRs={merged_prs},",
        f"bridge stars={bridge_stars},",
        f"go-walletconnect-bridge stars={wc_stars}",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"GitHub API error: {exc.code} {exc.reason}", file=sys.stderr)
        raise SystemExit(1)
