import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

BASE_URL = "https://api.github.com"


def github_request(
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Make an authenticated request to the GitHub REST API."""

    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is not configured.")

    if not GITHUB_REPO:
        raise ValueError("GITHUB_REPO is not configured.")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=headers,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


def get_recent_commits(limit: int = 10) -> list[dict[str, Any]]:
    """Return recent commits from the configured repository."""

    if limit <= 0:
        return []

    commits = github_request(
        f"/repos/{GITHUB_REPO}/commits",
        params={"per_page": min(limit, 100)},
    )

    return [
        {
            "sha": commit["sha"],
            "message": commit["commit"]["message"],
            "author": commit["commit"]["author"]["name"],
            "date": commit["commit"]["author"]["date"],
        }
        for commit in commits[:limit]
    ]


def get_open_pull_requests() -> list[dict[str, Any]]:
    """Return currently open pull requests."""

    pull_requests = github_request(
        f"/repos/{GITHUB_REPO}/pulls",
        params={
            "state": "open",
            "per_page": 100,
        },
    )

    return [
        {
            "number": pull_request["number"],
            "title": pull_request["title"],
            "author": pull_request["user"]["login"],
            "url": pull_request["html_url"],
        }
        for pull_request in pull_requests
    ]


def create_bug_issue(title: str, body: str) -> dict[str, Any]:
    """Create a new GitHub issue in the configured repository."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is not configured.")
    if not GITHUB_REPO:
        raise ValueError("GITHUB_REPO is not configured.")
    if not title.strip():
        raise ValueError("Issue title cannot be empty.")
    if not body.strip():
        raise ValueError("Issue body cannot be empty.")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.post(
        f"{BASE_URL}/repos/{GITHUB_REPO}/issues",
        headers=headers,
        json={
            "title": title,
            "body": body,
        },
        timeout=15,
    )
    response.raise_for_status()

    issue = response.json()

    return {
        "number": issue["number"],
        "title": issue["title"],
        "url": issue["html_url"],
        "state": issue["state"],
    }