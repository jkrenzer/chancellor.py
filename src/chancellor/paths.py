"""Locating the project and building paths inside it.

The project root is found by walking up from the data file: the nearest folder holding a
`pyproject.toml` or a `.git`, else the data file's own folder. Chancellor's
own location never takes part. Every configured path resolves against the root, must stay
inside it — symlinks included — and is stored repo-relative in POSIX form.

`output_path_for` is the only place a document's output path is constructed. Paths are never
parsed back into records.
"""

import os
from pathlib import Path, PurePosixPath

from .api import Model
from .errors import ConfigError

DATA_FILE = "chancellor.yaml"
"""Name of the data file found by walking up from the working directory."""

DATA_FILE_ENV = "CHANCELLOR_DATA"


def find_data_file(
    explicit: Path | None = None, start: Path | None = None
) -> Path | None:
    """The data file: `explicit`, else `$CHANCELLOR_DATA`, else the nearest `chancellor.yaml`."""
    if explicit is None and os.environ.get(DATA_FILE_ENV):
        explicit = Path(os.environ[DATA_FILE_ENV])
    if explicit is not None:
        if not explicit.is_file():
            raise ConfigError(f"Data file not found: {explicit}")
        return explicit.resolve()
    folder = (start or Path.cwd()).resolve()
    for candidate in (folder, *folder.parents):
        if (candidate / DATA_FILE).is_file():
            return candidate / DATA_FILE
    return None


def find_root(data_file: Path) -> Path:
    """Project root for a data file: the nearest folder upwards holding a `pyproject.toml` or a
    `.git`, else the data file's own folder. Nearest wins, so a `pyproject.toml` above the
    repository never takes the root out of it."""
    start = data_file.resolve().parent
    for folder in (start, *start.parents):
        if (folder / "pyproject.toml").exists() or (folder / ".git").exists():
            return folder
    return start


def confine(root: Path, path: str | PurePosixPath, *, setting: str = "path") -> Path:
    """Resolve a configured path against `root`; refuse one that leaves it."""
    candidate = Path(path)
    if candidate.is_absolute():
        raise ConfigError(f"{setting}: {path} must be relative to the project root")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ConfigError(
            f"{setting}: {path} resolves to {resolved}, outside the project root {root}"
        )
    return resolved


def relative(root: Path, path: Path) -> str:
    """`path` relative to `root`, in POSIX form."""
    return PurePosixPath(path.resolve().relative_to(root.resolve())).as_posix()


def template_suffix(template: str) -> str:
    """Output suffix of a template name: `decision.md.j2` gives `.md`."""
    name = PurePosixPath(template).name.removesuffix(".j2")
    return PurePosixPath(name).suffix


def output_path_for(root: Path, folder: str, record: Model, template: str) -> Path:
    """The output path of a record's document; the only place one is built."""
    directory = confine(root, folder, setting="folder")
    return directory / record.output_name(template_suffix(template))
