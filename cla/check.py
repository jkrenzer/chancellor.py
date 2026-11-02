"""Check that every author of a pull request has accepted the CLA.

Runs in CI from a checkout of the *base* branch, so a pull request cannot change the check
that judges it. Pull request data is read through the GitHub REST API with a read-only token
and is only parsed, never executed. Standard library only.

Environment: ``GITHUB_TOKEN``, ``GITHUB_REPOSITORY``, ``PR_NUMBER`` and optionally
``GITHUB_API_URL`` and ``GITHUB_STEP_SUMMARY``.

A commit author or co-author is covered when one of these holds:

- a record in ``cla/signatures/`` on the base branch has their GitHub id;
- an entity record in ``cla/entities/`` lists their GitHub id;
- the pull request adds their own record and was opened from their account;
- they are a bot, or the user who owns the repository.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

CLA_DIR = Path(__file__).resolve().parent
SIGNATURE_PREFIX = "cla/signatures/"
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
CO_AUTHOR_RE = re.compile(r"^Co-authored-by:\s*(.*?)\s*<([^>]+)>\s*$", re.M | re.I)
NOREPLY_RE = re.compile(r"^(\d+)\+[^@]+@users\.noreply\.github\.com$", re.I)


def front_matter(text: str) -> dict[str, str]:
    """Return the flat ``key: value`` pairs of a record's front matter."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    pairs = (line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def signed_ids(directory: Path) -> set[int]:
    """Return the GitHub ids of individual signature records on the base branch."""
    ids = set()
    for path in directory.glob("signatures/*.md"):
        ident = front_matter(path.read_text("utf-8")).get("github-id", "")
        if ident.isdigit():
            ids.add(int(ident))
    return ids


def entity_ids(directory: Path) -> set[int]:
    """Return the GitHub ids that entity records list in ``github-ids: [1, 2]``."""
    ids = set()
    for path in directory.glob("entities/*.md"):
        listed = front_matter(path.read_text("utf-8")).get("github-ids", "")
        ids.update(int(item) for item in re.findall(r"\d+", listed))
    return ids


class GitHub:
    """Minimal read-only client for the GitHub REST API."""

    def __init__(self, token: str, api: str) -> None:
        self.token = token
        self.api = api.rstrip("/")

    def get(self, url: str, raw: bool = False):
        """Return the decoded JSON, or the raw text, of a GET request."""
        if not url.startswith("https://"):
            url = f"{self.api}/{url.lstrip('/')}"
        accept = (
            "application/vnd.github.raw+json" if raw else "application/vnd.github+json"
        )
        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}", "Accept": accept},
        )
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
            body = response.read().decode("utf-8")
        return body if raw else json.loads(body)

    def pages(self, path: str) -> list:
        """Return all items of a paginated list endpoint."""
        items, page = [], 1
        while True:
            batch = self.get(f"{path}?per_page=100&page={page}")
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1


def new_signatures(
    gh: GitHub, files: list[dict], opener: dict, problems: list[str]
) -> set[int]:
    """Return the ids covered by signature records the pull request adds."""
    covered = set()
    for changed in files:
        path = changed["filename"]
        if not path.startswith(SIGNATURE_PREFIX):
            continue
        if changed["status"] != "added":
            problems.append(
                f"`{path}` is {changed['status']}; only new records may be added."
            )
            continue
        record = front_matter(gh.get(changed["contents_url"], raw=True))
        expected = f"{SIGNATURE_PREFIX}{opener['login'].lower()}.md"
        if path != expected or record.get("github-id") != str(opener["id"]):
            problems.append(
                f"`{path}` does not belong to @{opener['login']}, who opened this pull request. "
                "Everyone adds their own record in a pull request of their own."
            )
            continue
        covered.add(opener["id"])
    return covered


def uncovered_authors(commits: list[dict], covered: set[int]) -> dict[str, str]:
    """Map each uncovered author or co-author to the reason it is reported."""
    missing: dict[str, str] = {}
    for commit in commits:
        sha = commit["sha"][:7]
        author = commit.get("author")
        if author is None:
            email = commit["commit"]["author"]["email"]
            missing[email] = f"author email of {sha} is not linked to a GitHub account"
        elif author["type"] != "Bot" and author["id"] not in covered:
            missing[author["login"]] = f"author of {sha}"
        for name, email in CO_AUTHOR_RE.findall(commit["commit"]["message"]):
            noreply = NOREPLY_RE.match(email)
            if not noreply:
                missing[email] = (
                    f"co-author {name} of {sha}; use their GitHub noreply address in the trailer"
                )
            elif int(noreply.group(1)) not in covered:
                missing[email] = f"co-author {name} of {sha}"
    return missing


def check(gh: GitHub, repo: str, number: int, directory: Path) -> list[str]:
    """Return the problems found; an empty list means the pull request passes."""
    problems: list[str] = []
    opener = gh.get(f"repos/{repo}/pulls/{number}")["user"]
    owner = gh.get(f"repos/{repo}")["owner"]

    covered = signed_ids(directory) | entity_ids(directory)
    if owner["type"] == "User":
        covered.add(owner["id"])
    files = gh.pages(f"repos/{repo}/pulls/{number}/files")
    covered |= new_signatures(gh, files, opener, problems)

    commits = gh.pages(f"repos/{repo}/pulls/{number}/commits")
    missing = uncovered_authors(commits, covered)
    problems.extend(
        f"No CLA signature for `{who}` ({why})." for who, why in missing.items()
    )
    return problems


def main() -> None:
    """Run the check for the pull request named in the environment."""
    gh = GitHub(
        os.environ["GITHUB_TOKEN"],
        os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    problems = check(
        gh, os.environ["GITHUB_REPOSITORY"], int(os.environ["PR_NUMBER"]), CLA_DIR
    )
    if problems:
        summary = "\n".join(
            [
                "## CLA check failed",
                "",
                *(f"- {p}" for p in problems),
                "",
                "See `CONTRIBUTING.md`, section *Licensing of contributions*.",
            ]
        )
    else:
        summary = "## CLA check passed\n\nEvery author has accepted the CLA."
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write(summary + "\n")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
