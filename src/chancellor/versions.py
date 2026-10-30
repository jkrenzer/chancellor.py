"""Version schemes and absolute record IDs (0.1.0:D0036, 0.1.0:S0008).

A scheme (`chancellor.api.VersionScheme`) parses a version string into a sort key, or rejects
it. The built-in ones: `builtin.semver` (Semantic Versioning 2.0.0), `builtin.pep440` and
`builtin.free`, which accepts anything and orders nothing. Absolute IDs combine a
record-set version and a record ID in the configured format, `{version}:{id}` by default.
"""

import re
import string
from typing import Any, ClassVar

from packaging.version import InvalidVersion, Version

from .api import VersionScheme

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
"""The regular expression semver.org publishes for SemVer 2.0.0."""


def semver_key(text: str) -> tuple[Any, ...] | None:
    """Precedence key of a SemVer 2.0.0 version, or `None` if it does not parse. A release
    sorts after its pre-releases; numeric identifiers sort numerically and before alphanumeric
    ones; build metadata is ignored."""
    match = _SEMVER.match(text)
    if match is None:
        return None
    major, minor, patch, prerelease, _ = match.groups()
    release = (int(major), int(minor), int(patch))
    if prerelease is None:
        return (*release, 1, ())
    identifiers = tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in prerelease.split(".")
    )
    return (*release, 0, identifiers)


class SemverScheme(VersionScheme):
    """`builtin.semver`: Semantic Versioning 2.0.0, parsed and ordered by its own rules."""

    def key(self, text: str) -> Any | None:
        return semver_key(text)


class Pep440Scheme(VersionScheme):
    """`builtin.pep440`: Python's version scheme, parsed and ordered by `packaging`."""

    def key(self, text: str) -> Any | None:
        try:
            return Version(text)
        except InvalidVersion:
            return None


class FreeScheme(VersionScheme):
    """`builtin.free`: any version is accepted and nothing is ordered."""

    checks: ClassVar[bool] = False

    def key(self, text: str) -> Any | None:
        return text if text and ":" not in text and "/" not in text else None


SCHEME_ALIASES = {
    "semver": "builtin.semver",
    "pep440": "builtin.pep440",
    "free": "builtin.free",
}
"""Short scheme names from the versioning specification, for the built-in types."""


def absolute_id(version: str | None, record_id: str, form: str) -> str | None:
    """The absolute ID of a record, or `None` when the record set has no version."""
    return None if version is None else form.format(version=version, id=record_id)


def split_absolute(
    value: str, form: str, scheme: VersionScheme
) -> tuple[str, str] | None:
    """(version, id) when `value` is a local absolute ID in `form`, else `None`.

    The version part must be a version of the scheme; for `builtin.free` that is structural:
    no `:`, so `<project>:<version>:<id>` stays an external reference. A URL never is one.
    """
    if "://" in value:
        return None
    pattern = ""
    for literal, name, _, _ in string.Formatter().parse(form):
        pattern += re.escape(literal)
        if name == "version":
            pattern += r"(?P<version>[^:]+?)"
        elif name == "id":
            pattern += r"(?P<id>[^:]+)"
    match = re.fullmatch(pattern, value)
    if match is None or "version" not in match.groupdict():
        return None
    version, record_id = match.group("version"), match.group("id")
    if not scheme.is_version(version):
        return None
    return version, record_id
