"""Write a CLA signature record for the current contributor.

Prefills the record from git and the GitHub CLI, shows it, and writes it to
``cla/signatures/<github-login>.md`` after confirmation. Standard library only, so it runs
without the project's virtual environment.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
import textwrap
import urllib.request
from pathlib import Path

CLA_DIR = Path(__file__).resolve().parent
ROOT = CLA_DIR.parent
SIGNATURES = CLA_DIR / "signatures"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def run(*cmd: str) -> str | None:
    """Return a command's stripped stdout, or None if it fails or is missing."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=ROOT
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def cla_version() -> str:
    """Read the agreement version from the first 'Version x.y' line of CLA.md."""
    match = re.search(
        r"^Version (\d+\.\d+)", (ROOT / "CLA.md").read_text("utf-8"), re.M
    )
    if not match:
        sys.exit("Could not find the agreement version in CLA.md.")
    return match.group(1)


def github_account(login: str | None) -> tuple[str, int]:
    """Return (login, numeric id), from `gh` if logged in, else from the public API."""
    if login is None:
        found = run("gh", "api", "user", "--jq", '.login + " " + (.id | tostring)')
        if found:
            name, ident = found.split()
            return name, int(ident)
        login = input("GitHub login: ").strip()
    if not LOGIN_RE.match(login):
        sys.exit(f"Not a valid GitHub login: {login!r}")
    url = f"https://api.github.com/users/{login}"
    with urllib.request.urlopen(
        url, timeout=10
    ) as response:  # nosec B310: fixed https host
        data = json.load(response)
    return data["login"], int(data["id"])


def render(name: str, login: str, ident: int, version: str, date: str) -> str:
    """Return the signature record as Markdown with front matter."""
    statement = textwrap.fill(
        f"I, {name}, have read the Chancellor Individual Contributor Licence Agreement, "
        f"version {version} (git tag cla-v{version}), and accept it for all my "
        "Contributions to Chancellor.",
        width=100,
    )
    return (
        "---\n"
        f"name: {json.dumps(name, ensure_ascii=False)}\n"
        f"github-login: {login}\n"
        f"github-id: {ident}\n"
        "agreement: CLA.md\n"
        f'version: "{version}"\n'
        f"date: {date}\n"
        "---\n\n"
        f"{statement}\n"
    )


def main() -> None:
    """Parse arguments, build the record, confirm and write it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", help="name to record (default: git config user.name)")
    parser.add_argument("--login", help="GitHub login (default: from `gh api user`)")
    parser.add_argument("--yes", action="store_true", help="write without asking")
    args = parser.parse_args()

    name = args.name or run("git", "config", "user.name")
    if not name:
        name = input("Name to record (may be a pseudonym): ").strip()
    if not name or "\n" in name:
        sys.exit("A single-line name is required.")
    login, ident = github_account(args.login)
    version = cla_version()
    date = datetime.datetime.now(datetime.UTC).date().isoformat()
    record = render(name, login, ident, version, date)
    target = SIGNATURES / f"{login.lower()}.md"

    if target.exists():
        sys.exit(f"{target.relative_to(ROOT)} already exists. Nothing to do.")
    print(f"This record will be written to {target.relative_to(ROOT)}:\n\n{record}")
    print("Adding it to a pull request from your GitHub account accepts CLA.md.")
    if not args.yes and input("Write it? [y/N] ").strip().lower() not in {"y", "yes"}:
        sys.exit("Aborted. Nothing was written.")
    SIGNATURES.mkdir(exist_ok=True)
    target.write_text(record, "utf-8")
    print(
        "\nWritten. Next:\n"
        f"  git add {target.relative_to(ROOT)}\n"
        '  git commit -m "chore(cla): sign contributor licence agreement"'
    )


if __name__ == "__main__":
    main()
