"""The lock file: what the last build saw.

The lock records the renderer version, the environment digests, the resolved provider set,
the degradations of the build, and per document its digest parts,
the digest of the bytes written and the data files it came from. It is JSON with sorted keys,
so it diffs well and serializes the same everywhere.

A lock that cannot be read, or carries another `_api` version — such as one written before
chancellor knew providers — is ignored and everything is rebuilt; it is never an error.
"""

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

LOCK_API_VERSION = "2"
"""2: the whole fingerprint map in `environment`, no per-document `feeding` (0.1.0:D0018)."""


class _Lock(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LockApi(_Lock):
    version: Literal["2"]
    kind: Literal["chancellor_lock"]


class LockProvider(_Lock):
    name: str
    origin: str
    type: Literal["code", "declarative"]
    fingerprint: str
    kinds: list[str] = Field(default_factory=list)


class LockDegradation(_Lock):
    code: str
    subject: str
    message: str


class LockDocument(_Lock):
    id: str
    kind: str
    part: str
    data_hash: str
    input_hash: str
    parts: dict[str, str]
    output: str
    sources: list[str] = Field(default_factory=list)


class LockEnvironment(_Lock):
    api: str
    config: str
    providers: str
    fingerprints: dict[str, str] = Field(default_factory=dict)


class Lock(_Lock):
    """Contents of the lock file."""

    api: LockApi = Field(alias="_api")
    renderer: str
    environment: LockEnvironment
    providers: list[LockProvider]
    degradations: list[LockDegradation] = Field(default_factory=list)
    cli_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="`--set` values the build that wrote this lock applied, by dotted key.",
    )
    documents: dict[str, LockDocument] = Field(default_factory=dict)

    def text(self) -> str:
        data = self.model_dump(mode="json", by_alias=True)
        return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_lock_paths(path: Path) -> set[str]:
    """Document paths of a lock that cannot be used, read best effort.

    Only for orphan detection after a lock was ignored (another `_api` version, damage): its
    hashes are never trusted, so nothing it lists is deleted on its word.
    """
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return set()
    documents = data.get("documents") if isinstance(data, dict) else None
    return (
        {rel for rel in documents if isinstance(rel, str)}
        if isinstance(documents, dict)
        else set()
    )


def read_lock(path: Path) -> Lock | None:
    """The lock at `path`, or `None` when absent, unreadable or of another version."""
    if not path.is_file():
        return None
    try:
        return Lock.model_validate(json.loads(path.read_text("utf-8")))
    except (OSError, ValueError, ValidationError) as exc:
        logger.info(
            "ignoring lock %s, everything is rebuilt: %s",
            path,
            str(exc).split("\n", maxsplit=1)[0],
        )
        return None
