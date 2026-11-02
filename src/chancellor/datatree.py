"""Reading the data tree from one file or several.

The top level holds exactly three kinds of key: `_api/<module>`, `config/<module>`, and one
section per record kind. Several files merge by one rule: mappings merge key-wise, lists in
kind sections concatenate, and a value defined in two files is an error naming both. File
layout is not content; provenance is kept per section and per record for `explain` and the
lock, but never enters a digest.
"""

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigError, InputError
from .keys import ModuleKeys
from .paths import confine, relative
from .yamlio import load as load_yaml

logger = logging.getLogger(__name__)

MODULE_FACETS = ("_api", "config", "meta")
"""Top-level keys holding one entry per tool; every other top-level key is a record kind."""

CONFIG_FACETS = ("_api", "config")
"""Facets holding configuration; a value defined twice there is a configuration error."""

NEW_SHAPE = """\
_api:
  {api}:
    version: "2.0.0"
    kind: project_records
config:
  {config}:
    ...
decisions:
  core: {{...}}
  records: [...]"""


@dataclass
class DataTree:
    """The merged data tree and where each part of it came from."""

    data: dict[str, Any]
    files: list[str]
    section_origins: dict[str, list[str]] = field(default_factory=dict)
    record_origins: dict[tuple[str, str], str] = field(default_factory=dict)
    raw: list[tuple[str, dict[str, Any]]] = field(default_factory=list, repr=False)
    kind_files: dict[str, str] = field(default_factory=dict)
    """Data files of single kinds (0.1.0:D0019), by file, naming their kind."""
    missing_kind_data: dict[str, str] = field(default_factory=dict)
    """Kinds whose configured data file does not exist, with that file."""

    def sections(self) -> dict[str, Any]:
        """Every top-level key except the module facets."""
        return {k: v for k, v in self.data.items() if k not in MODULE_FACETS}

    def module(self, facet: str, key: str) -> dict[str, Any]:
        value = self.data.get(facet, {}).get(key, {})
        return value if isinstance(value, dict) else {}


def check_scoped(data: Any, where: str, keys: ModuleKeys) -> dict[str, Any]:
    """Refuse anything but the scoped layout, naming the new shape for the old one."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{where}: the data tree must be a mapping")
    for facet in MODULE_FACETS:
        value = data.get(facet)
        if value is None:
            continue
        unscoped = not isinstance(value, dict) or any(
            not isinstance(item, dict) for item in value.values()
        )
        if unscoped:
            shape = NEW_SHAPE.format(api=keys.api, config=keys.config)
            raise ConfigError(
                f"{where}: {facet} uses the unscoped layout, which is no longer read. "
                f"Each tool owns one key below {facet}; write it as:\n{shape}"
            )
    return data


@dataclass(frozen=True)
class DataLocation:
    """Where a kind's data lives: a file and the key path to the kind's section in it (0.1.0:D0019).

    A per-kind data file has an empty key path: the whole file is the kind's section. A file
    shared by several kinds (future) gives the path to the section's key; everything below
    already walks `key`, so only `location_for` changes.
    """

    file: str
    key: tuple[str, ...] = ()


def location_for(kind_config: Any) -> DataLocation | None:
    """The data location configured for one kind, or `None` when its data stays in the tree."""
    file = getattr(kind_config, "data", None)
    if not file:
        return None
    # shared data file (future, 0.1.0:D0019): read the key path here, e.g. from a `key` setting
    # (`records.decisions`), split on dots, and return DataLocation(file, tuple(parts)).
    return DataLocation(file=file)


def merge_kind_data(
    tree: "DataTree", root: Path, kind: str, location: DataLocation
) -> None:
    """Merge a kind's data file into the tree, with provenance, under the usual merge rules."""
    path = confine(root, location.file, setting=f"kinds.{kind}.data")
    name = relative(root, path)
    if name in tree.files:
        raise ConfigError(
            f"kinds.{kind}.data: {name} is also read as a whole data tree (main file or "
            "include); a kind's data file holds that kind's section only"
        )
    claimed = tree.kind_files.get(name)
    # shared data file (future, 0.1.0:D0019): several kinds may name one file once each brings its
    # own key path; then compare (file, key) pairs here instead of files.
    if claimed is not None:
        raise ConfigError(
            f"kinds.{kind}.data: {name} is already the data file of {claimed}"
        )
    tree.kind_files[name] = kind
    if not path.is_file():
        # No data yet, by design; the build guards existing documents of the kind (a typo in
        # the path must not delete them, 0.1.0:D0035).
        logger.info(
            "kinds.%s.data: %s does not exist yet; the kind has no data", kind, name
        )
        tree.missing_kind_data[kind] = name
        return
    section: Any = load_yaml(path, error=InputError)
    for depth, part in enumerate(location.key):
        if not isinstance(section, dict) or part not in section:
            where = ".".join(location.key[: depth + 1])
            raise InputError(f"kinds.{kind}.data: {name} has no key {where}")
        section = section[part]
    if section is None:
        return
    if not isinstance(section, dict):
        raise InputError(
            f"kinds.{kind}.data: {name} must hold a mapping with core and records"
        )
    wrapped = {kind: section}
    _note_origins(tree, wrapped, name)
    _merge(tree.data, wrapped, name, (), tree)
    tree.raw.append((name, wrapped))


def resolve_includes(root: Path, main: Path, includes: list[str]) -> list[Path]:
    """Data files named in `include`: files, or folders whose `*.yaml` files load by name."""
    result: list[Path] = []
    for entry in includes:
        path = confine(root, entry, setting="include")
        if path.is_dir():
            result.extend(
                sorted(
                    p
                    for p in path.iterdir()
                    if p.suffix in (".yaml", ".yml") and p.is_file()
                )
            )
        elif path.is_file():
            result.append(path)
        else:
            raise ConfigError(f"include: {entry} does not exist")
    seen = {main.resolve()}
    unique = []
    for path in result:
        if path.resolve() not in seen:
            seen.add(path.resolve())
            unique.append(path)
    return unique


def read_tree(
    root: Path,
    main: Path,
    main_data: dict[str, Any],
    includes: list[str],
    keys: ModuleKeys,
) -> DataTree:
    """Merge the main file and its includes into one tree."""
    paths = [main, *resolve_includes(root, main, includes)]
    tree = DataTree(data={}, files=[relative(root, p) for p in paths])
    for path, name in zip(paths, tree.files):
        data = (
            main_data
            if path == main
            else check_scoped(load_yaml(path, error=ConfigError), name, keys)
        )
        _note_origins(tree, data, name)
        _merge(tree.data, data, name, (), tree)
        tree.raw.append((name, data))
    return tree


def _note_origins(tree: DataTree, data: dict[str, Any], name: str) -> None:
    for section, value in data.items():
        tree.section_origins.setdefault(section, []).append(name)
        if section in MODULE_FACETS:
            continue
        records = value.get("records") if isinstance(value, dict) else None
        if isinstance(value, dict) and isinstance(value.get("core"), dict):
            core_id = value["core"].get("id")
            if isinstance(core_id, str):
                tree.record_origins[(section, core_id)] = name
        for item in records if isinstance(records, list) else []:
            record_id = item.get("id") if isinstance(item, dict) else None
            if not isinstance(record_id, str):
                continue
            first = tree.record_origins.get((section, record_id))
            if first is not None:
                where = f"{first} and {name}" if first != name else f"{name} twice"
                raise InputError(
                    f"Duplicate record ID {record_id} in {section}: in {where}"
                )
            tree.record_origins[(section, record_id)] = name


def _merge(
    target: dict[str, Any],
    source: dict[str, Any],
    name: str,
    path: tuple[str, ...],
    tree: DataTree,
) -> None:
    for key, value in source.items():
        here = (*path, str(key))
        if key not in target:
            target[key] = deepcopy(value)
            continue
        existing = target[key]
        if isinstance(existing, dict) and isinstance(value, dict):
            _merge(existing, value, name, here, tree)
        elif (
            isinstance(existing, list)
            and isinstance(value, list)
            and here[0] not in MODULE_FACETS
        ):
            existing.extend(deepcopy(value))
        else:
            first = _first_file(tree, here) or "an earlier file"
            # Configuration defined twice is a configuration error; record data, an input error.
            error = ConfigError if here[0] in CONFIG_FACETS else InputError
            raise error(f"{'.'.join(here)} is defined in {first} and in {name}")


def _first_file(tree: DataTree, here: tuple[str, ...]) -> str | None:
    """The earliest file already merged that defines the value at `here`."""
    for name, data in tree.raw:
        node: Any = data
        for part in here:
            if not isinstance(node, dict) or part not in node:
                break
            node = node[part]
        else:
            return name
    return None
