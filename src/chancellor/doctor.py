"""Health checks of a project that a build does not fail on, or fails on too late to explain.

Problems make `doctor` exit 1; notes are informational.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import get_args

from pydantic import BaseModel

from .api import MANIFEST_FILE
from .build import plan, untracked_documents
from .config import bootstrap
from .datatree import check_scoped
from .errors import ChancellorError, ConfigError, InputError
from .keys import ModuleKeys
from .lock import read_lock, read_lock_paths
from .paths import confine, find_data_file, find_root, relative
from .project import Project
from .registry import Registry
from .yamlio import load as load_yaml

PYMARKDOWN_WIDTH = ("tool", "pymarkdown", "plugins", "md013", "line_length")


@dataclass
class Report:
    problems: list[str] = field(default_factory=list)
    """Configuration problems: exit 1."""
    input_problems: list[str] = field(default_factory=list)
    """Record data problems, such as one-sided links: exit 2."""
    notes: list[str] = field(default_factory=list)


def diagnose(data_file: Path | None, keys: ModuleKeys | None = None) -> Report:
    """Run every check; load errors become problems instead of exceptions."""
    keys = keys or ModuleKeys()
    report = Report()
    found = find_data_file(data_file)
    if found is None:
        report.problems.append(
            "No chancellor.yaml found; pass --data or set CHANCELLOR_DATA"
        )
        return report
    root = find_root(found)
    _check_declared_providers(found, root, keys, report)
    if report.problems:
        return report
    try:
        project = Project.load(found, keys=keys)
    except InputError as exc:
        report.input_problems.append(str(exc))
        return report
    except ChancellorError as exc:
        report.problems.append(str(exc))
        return report
    _check_sections(project, report)
    _check_links(project, report)
    for kind, record_id, ref in project.historic_refs:
        report.notes.append(
            f"historic reference: {kind}.{record_id} refers to {ref}; the record set is "
            f"version {project.record_set_version or '(none set)'}"
        )
    scheme = project.version_scheme
    if scheme is not None and scheme.checks and project.record_set_version is None:
        report.notes.append(
            f"meta.{project.keys.meta}.version is not set although the versioning scheme is "
            f"{project.config.versioning.scheme}; records have no absolute IDs"
        )
    for missing in undescribed_fields(project.registry):
        report.notes.append(f"field without description: {missing}")
    _check_width(project, report)
    _check_outputs(project, report)
    for degradation in project.degradations:
        report.notes.append(
            f"degradation {degradation.code}: {degradation.subject}: "
            f"{degradation.message}"
        )
    return report


def _check_declared_providers(
    found: Path, root: Path, keys: ModuleKeys, report: Report
) -> None:
    try:
        main = check_scoped(
            load_yaml(found, error=ConfigError), relative(root, found), keys
        )
        boot = bootstrap(main, keys, relative(root, found))
    except ChancellorError as exc:
        report.problems.append(str(exc))
        return
    for entry in boot.providers:
        try:
            folder = confine(root, entry.path, setting=f"providers[{entry.name}].path")
        except ChancellorError as exc:
            report.problems.append(str(exc))
            continue
        if not (folder / MANIFEST_FILE).is_file():
            report.problems.append(
                f"provider {entry.name} is declared in config but {entry.path}/{MANIFEST_FILE} "
                "is missing"
            )


def _check_sections(project: Project, report: Report) -> None:
    assert project.tree is not None
    for name in sorted(set(project.tree.sections()) - set(project.registry.kinds)):
        report.notes.append(
            f"section {name} belongs to no registered kind; chancellor ignores it"
        )


def undescribed_fields(registry: Registry) -> list[str]:
    """Fields of every registered kind's models, nested models included, without a description.

    Field descriptions are what authors and agents read in `schema`, so every field should have one.
    """
    missing: list[str] = []
    seen: set[type] = set()

    def walk(model: type[BaseModel], where: str) -> None:
        if model in seen:
            return
        seen.add(model)
        for name, info in model.model_fields.items():
            if not info.description:
                missing.append(f"{where}.{name}")
            for nested in _models_in(info.annotation):
                walk(nested, f"{where}.{name}")

    for kind, spec in sorted(registry.kinds.items()):
        for part in ("records", "core_document"):
            model = spec.model if part == "records" else spec.core_model
            if model is not None:
                walk(model, f"{kind}.{model.__name__}")
    return missing


def _models_in(annotation: object) -> list[type[BaseModel]]:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]
    return [m for arg in get_args(annotation) for m in _models_in(arg)]


def _current_id(project: Project, value: str) -> str | None:
    """The record a reference value points to now: bare or current absolute; else `None`."""
    kind_of = project.classify_ref(value)
    return (
        kind_of[0]
        if kind_of is not None and kind_of[2] in ("bare", "current")
        else None
    )


def _check_links(project: Project, report: Report) -> None:
    """One-sided links (a problem) and records nothing references (a note)."""
    referenced: set[str] = set()
    for record_id, (kind, record) in sorted(project.records.items()):
        refs = project.resolved_refs(record)
        referenced.update(refs)
        for ref_field, inverse in type(record).inverse_refs.items():
            for value in getattr(record, ref_field, None) or []:
                target_id = _current_id(project, value)
                if target_id is None or target_id not in project.records:
                    continue
                target = project.records[target_id][1]
                if inverse not in type(target).model_fields:
                    continue
                listed = {
                    _current_id(project, v) for v in getattr(target, inverse) or []
                }
                if record_id not in listed:
                    report.input_problems.append(
                        f"one-sided link: {kind}.{record_id}.{ref_field} lists {target_id}, but "
                        f"{target_id}.{inverse} does not list {record_id}"
                    )
    cores = {
        section.core.id
        for section in project.sections.values()
        if section.core is not None
    }
    for record_id, (kind, _) in sorted(project.records.items()):
        if record_id not in referenced and record_id not in cores:
            report.notes.append(
                f"unreferenced: {kind}.{record_id} is referenced by no record"
            )


def _check_width(project: Project, report: Report) -> None:
    pyproject = project.root / "pyproject.toml"
    if not pyproject.is_file():
        return
    try:
        node = tomllib.loads(pyproject.read_text("utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        report.notes.append(f"pyproject.toml not readable: {exc}")
        return
    for key in PYMARKDOWN_WIDTH:
        if not isinstance(node, dict) or key not in node:
            return
        node = node[key]
    if node != project.config.wrap_width:
        report.problems.append(
            f"wrap_width is {project.config.wrap_width}, but [tool.pymarkdown] "
            f"plugins.md013.line_length is {node}; rendered documents would fail that lint"
        )


def _check_outputs(project: Project, report: Report) -> None:
    built = plan(project)
    planned = {d.rel for d in built.documents}
    lock = read_lock(built.lock_path)
    stale = read_lock_paths(built.lock_path) if lock is None else set()
    if lock is None:
        report.notes.append("no usable lock; the next build renders everything")
    lock_paths = set(lock.documents) if lock is not None else stale
    for rel in sorted(lock_paths - planned):
        report.notes.append(f"orphan: {rel} is in the lock but no record produces it")
    for rel in untracked_documents(project, planned | lock_paths):
        # A stale document chancellor no longer knows; a problem to act on (exit 1, 0.1.0:D0035).
        report.problems.append(
            f"untracked: {rel} is named like a document of its folder, but no record "
            "produces it and no lock lists it; delete it or restore its record"
        )
