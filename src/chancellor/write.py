"""The one function that writes into the project tree.

Nothing else in chancellor writes a file the build owns. Step 7 of the release plan replaces
the body with propose and apply (staging inside the repository, backups, journal, recover);
callers keep calling `apply`.
"""

from collections.abc import Iterable, Mapping
from pathlib import Path


def apply(writes: Mapping[Path, bytes], deletes: Iterable[Path] = ()) -> None:
    """Write files (creating folders) and delete files, in that order."""
    for path, content in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for path in deletes:
        path.unlink(missing_ok=True)
