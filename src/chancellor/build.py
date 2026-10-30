"""Planning and running a build, incrementally against the lock.

Every document chancellor owns is planned with its digest parts. A document is rendered
again when its `input_hash` moved, when it has no lock entry, or when the file on disk no
longer matches the bytes the lock says were written. Otherwise its rendering is skipped. A
cold lock and an incremental build therefore produce the same bytes.

Documents in the lock that the plan no longer produces are orphans: removed when the file is
still what chancellor wrote, reported and left alone when someone changed it.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .api import Degradation, Model
from .canonical import digest, digest_of, is_current
from .errors import ConfigError
from .hashing import (
    PARTS,
    DocumentInputs,
    Environment,
    document_inputs,
    renderer_version,
)
from .lock import (
    LOCK_API_VERSION,
    Lock,
    LockApi,
    LockDegradation,
    LockDocument,
    LockEnvironment,
    LockProvider,
    read_lock,
    read_lock_paths,
)
from .paths import confine, relative, template_suffix
from .project import Project
from .rendering import render_document
from .write import apply

Status = Literal[
    "new", "changed", "modified", "unchanged", "removed", "orphan", "untracked"
]
"""`orphan`: in the lock, produced by no record, edited or not provably unchanged, so kept.
`untracked`: in a kind's output folder, named like its documents, known to no lock; kept."""

SNAPSHOT_KIND = "_snapshot"


@dataclass
class PlannedDocument:
    """One document the build owns."""

    path: Path
    rel: str
    kind: str
    part: str
    record: Model | None
    template: str | None
    inputs: DocumentInputs
    sources: list[str]

    @property
    def id(self) -> str:
        return self.record.id if self.record is not None else SNAPSHOT_KIND


@dataclass
class BuildResult:
    """What a build found and, unless checking, did."""

    statuses: list[tuple[str, Status]]
    lock_changed: bool
    degradations: list[Degradation]
    written: bool

    @property
    def drift(self) -> bool:
        """Whether the build changes (or would change) anything; untracked files never count,
        since chancellor does not own them."""
        return self.lock_changed or any(
            s not in ("unchanged", "untracked") for _, s in self.statuses
        )


@dataclass
class Plan:
    documents: list[PlannedDocument]
    environment: Environment
    lock_path: Path
    snapshot: str | None = None
    rendered: dict[str, str] = field(default_factory=dict)
    cli_overrides: dict[str, Any] = field(default_factory=dict)


def plan(project: Project) -> Plan:
    """Every document of the project with its digest parts."""
    environment = Environment.of(project)
    documents: list[PlannedDocument] = []
    seen: dict[str, str] = {}
    tree = project.tree
    for kind, section in sorted(project.sections.items()):
        spec = project.registry.kinds[kind]
        for part, record in section.documents():
            template = spec.template(part)  # type: ignore[arg-type]
            path = project.document_path(kind, record)
            rel = relative(project.root, path)
            if rel in seen:
                raise ConfigError(
                    f"{record.id} and {seen[rel]} would both be written to {rel}"
                )
            seen[rel] = record.id
            sources = []
            if tree is not None:
                origin = tree.record_origins.get((kind, record.id))
                sources = (
                    [origin] if origin else list(tree.section_origins.get(kind, []))
                )
            documents.append(
                PlannedDocument(
                    path=path,
                    rel=rel,
                    kind=kind,
                    part=part,
                    record=record,
                    template=template,
                    inputs=document_inputs(project, environment, record, template),
                    sources=sources,
                )
            )
    result = Plan(
        documents=documents,
        environment=environment,
        lock_path=confine(project.root, project.config.lock, setting="lock"),
        cli_overrides=dict(project.cli_overrides),
    )
    if project.config.snapshot:
        result.snapshot = _plan_snapshot(project, environment, documents)
    return result


def _plan_snapshot(
    project: Project, environment: Environment, documents: list[PlannedDocument]
) -> str:
    path = confine(project.root, project.config.snapshot, setting="snapshot")
    data = {
        kind: {
            **(
                {"core": section.core.model_canonicalize()}
                if section.core is not None
                else {}
            ),
            "records": [record.model_canonicalize() for record in section.records],
        }
        for kind, section in sorted(project.sections.items())
    }
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    parts = {name: digest_of(None) for name in PARTS}
    parts.update(data=digest_of(data), config=environment.config, api=environment.api)
    rel = relative(project.root, path)
    documents.append(
        PlannedDocument(
            path=path,
            rel=rel,
            kind=SNAPSHOT_KIND,
            part=SNAPSHOT_KIND,
            record=None,
            template=None,
            inputs=DocumentInputs(parts=parts),
            sources=list(project.tree.files if project.tree else []),
        )
    )
    return text


def render(project: Project, document: PlannedDocument, built: Plan) -> str:
    """The document's text."""
    if document.record is None:
        assert built.snapshot is not None
        return built.snapshot
    assert document.template is not None
    return render_document(
        document.record,
        document.template,
        registry=project.registry,
        formatter=project.formatter(),
        context=project.format_context(),
        data_hash=document.inputs.parts["data"],
        refs=project.ref_context(document.record),
        extras=project.template_extras(document.record),
    )


def run(project: Project, *, check: bool = False) -> BuildResult:
    """Build every document; with `check`, write nothing and only report."""
    built = plan(project)
    old = read_lock(built.lock_path)
    old_documents = old.documents if old else {}
    statuses: list[tuple[str, Status]] = []
    writes: dict[Path, bytes] = {}
    entries: dict[str, LockDocument] = {}
    for document in built.documents:
        entry = old_documents.get(document.rel)
        on_disk = document.path.read_bytes() if document.path.is_file() else None
        current = (
            entry is not None
            and entry.input_hash == document.inputs.input_hash
            and is_current(entry.output)
        )
        if current and on_disk is not None and digest(on_disk) == entry.output:
            output = entry.output
            status: Status = "unchanged"
        else:
            content = render(project, document, built).encode("utf-8")
            output = digest(content)
            if on_disk == content:
                status = "unchanged"
            else:
                status = (
                    "new"
                    if on_disk is None
                    else ("changed" if not current else "modified")
                )
                writes[document.path] = content
        statuses.append((document.rel, status))
        entries[document.rel] = _lock_entry(document, output)
    deletes = []
    _settle_leftovers(project, built, old, entries, statuses, deletes)
    degradations = _unique(built.environment.degradations)
    lock = _lock(project, built, entries, degradations)
    old_text = built.lock_path.read_text("utf-8") if built.lock_path.is_file() else None
    lock_changed = lock.text() != old_text
    if not check:
        if lock_changed:
            writes[built.lock_path] = lock.text().encode("utf-8")
        apply(writes, deletes)
    return BuildResult(
        statuses=statuses,
        lock_changed=lock_changed,
        degradations=degradations,
        written=not check,
    )


def untracked_documents(project: Project, known: set[str]) -> list[str]:
    """Files in a kind's output folder named like that kind's documents (`<ID>…<suffix>`, the
    ID matching the kind's pattern) that neither the plan nor any lock knows."""
    return [rel for _, rel in untracked_by_kind(project, known)]


def untracked_by_kind(project: Project, known: set[str]) -> list[tuple[str, str]]:
    """`untracked_documents`, each with its kind."""
    found: list[tuple[str, str]] = []
    for kind, spec in sorted(project.registry.kinds.items()):
        pattern = spec.id_pattern
        folder = confine(project.root, spec.folder, setting=f"kinds.{kind}.folder")
        if pattern is None or not folder.is_dir():
            continue
        suffix = template_suffix(spec.templates.records)
        for path in sorted(folder.iterdir()):
            if not path.is_file() or not path.name.endswith(suffix):
                continue
            record_id = path.name.removesuffix(suffix).split("-", 1)[0]
            rel = relative(project.root, path)
            if pattern.fullmatch(record_id) and rel not in known:
                found.append((kind, rel))
    return found


def _settle_leftovers(
    project: Project,
    built: Plan,
    old: Lock | None,
    entries: dict[str, LockDocument],
    statuses: list[tuple[str, Status]],
    deletes: list[Path],
) -> None:
    """Documents the plan no longer produces: remove what chancellor provably wrote, keep the
    rest as orphans, and report files named like documents that nothing knows as untracked.
    A kind whose data file is missing keeps all its documents, with a degradation
    (0.1.0:D0035)."""
    old_documents = old.documents if old else {}
    missing = dict(project.tree.missing_kind_data) if project.tree is not None else {}
    guarded: dict[str, list[str]] = {}
    for rel, entry in sorted(old_documents.items()):
        if rel in entries:
            continue
        path = confine(project.root, rel, setting="lock document")
        if entry.kind in missing and path.is_file():
            # The kind's data file is missing: never delete its documents on that basis.
            statuses.append((rel, "orphan"))
            guarded.setdefault(entry.kind, []).append(rel)
        elif path.is_file() and digest(path.read_bytes()) == entry.output:
            statuses.append((rel, "removed"))
            deletes.append(path)
        elif path.is_file():
            statuses.append((rel, "orphan"))
    stale = (
        read_lock_paths(built.lock_path)
        if old is None and built.lock_path.is_file()
        else set()
    )
    for rel in sorted(stale - set(entries)):
        # A lock that could not be used still names what it wrote; never trusted, so
        # the file is reported and kept rather than deleted.
        if confine(project.root, rel, setting="lock document").is_file():
            statuses.append((rel, "orphan"))
    known = set(entries) | set(old_documents) | stale
    for kind, rel in untracked_by_kind(project, known):
        statuses.append((rel, "untracked"))
        if kind in missing:
            guarded.setdefault(kind, []).append(rel)
    for kind, rels in sorted(guarded.items()):
        built.environment.degradations.append(
            Degradation(
                "missing-data-file",
                kind,
                f"kinds.{kind}.data names {missing[kind]}, which does not exist, but "
                f"{len(rels)} document(s) of {kind} do; they are kept, not deleted. Check the "
                "path, or delete the documents yourself if the kind has no data any more",
            )
        )


def _unique(degradations: list[Degradation]) -> list[Degradation]:
    return sorted(set(degradations), key=lambda d: (d.code, d.subject, d.message))


def _lock_entry(document: PlannedDocument, output: str) -> LockDocument:
    return LockDocument(
        id=document.id,
        kind=document.kind,
        part=document.part,
        data_hash=document.inputs.parts["data"],
        input_hash=document.inputs.input_hash,
        parts=document.inputs.parts,
        output=output,
        sources=document.sources,
    )


def _lock(
    project: Project,
    built: Plan,
    entries: dict[str, LockDocument],
    degradations: list[Degradation],
) -> Lock:
    environment = built.environment
    providers = [
        LockProvider(
            name=provider.name,
            origin=provider.origin,
            type="code" if provider.code else "declarative",
            fingerprint=environment.fingerprints[provider.name],
            kinds=sorted(provider.manifest.kinds),
        )
        for provider in project.registry.providers
    ]
    if project.root_model is not None:
        providers.append(
            LockProvider(
                name="data_model",
                origin=project.root_model.origin,
                type="code",
                fingerprint=project.root_model.fingerprint,
                kinds=sorted(project.sections),
            )
        )
    return Lock(
        api=LockApi(version=LOCK_API_VERSION, kind="chancellor_lock"),
        renderer=renderer_version(),
        cli_overrides=dict(project.cli_overrides),
        environment=LockEnvironment(
            api=environment.api,
            config=environment.config,
            providers=environment.providers_digest,
            fingerprints=environment.fingerprints,
        ),
        providers=providers,
        degradations=[
            LockDegradation(code=d.code, subject=d.subject, message=d.message)
            for d in degradations
        ],
        documents=dict(sorted(entries.items())),
    )


# Explain


def explain(project: Project, record_id: str) -> list[str]:
    """Lines naming, per document of `record_id`, the digest parts that moved since the lock."""
    built = plan(project)
    old = read_lock(built.lock_path)
    documents = [d for d in built.documents if d.id == record_id]
    if not documents:
        known = sorted({d.id for d in built.documents} - {SNAPSHOT_KIND})
        raise ConfigError(f"No document for {record_id}; known IDs: {', '.join(known)}")
    lines: list[str] = []
    for document in documents:
        lines.append(f"{document.rel} ({document.kind}, {document.part})")
        lines.append(f"  sources: {', '.join(document.sources) or '-'}")
        entry = old.documents.get(document.rel) if old else None
        if entry is None:
            lines.append("  not in the lock: rendered as new")
            continue
        if entry.sources != document.sources:
            lines.append(f"  sources moved from {', '.join(entry.sources) or '-'}")
        moved = [p for p in PARTS if entry.parts.get(p) != document.inputs.parts.get(p)]
        if not moved:
            lines.append("  unchanged: every digest part matches the lock")
        for name in moved:
            lines.append(f"  {name}: {_explain_part(name, old, built)}")
    return lines


def _explain_part(name: str, old: Lock | None, built: Plan) -> str:
    if name == "providers":
        return _explain_providers(old, built)
    if name == "config":
        return _explain_config(old, built)
    descriptions = {
        "data": "the record's own data changed",
        "refs": "something it reads of another record changed (a reference's declared "
        "`depends`, or a generated index)",
        "files": "a hashed file changed",
        "templates": "a template it uses changed",
        "meta": "the record-set version or the absolute-ID format changed",
        "api": "the data format or the renderer changed (chancellor's version or source, the "
        "Python version, or a library that shapes the output)",
    }
    return descriptions[name]


def _explain_providers(old: Lock | None, built: Plan) -> str:
    """Name which fingerprints moved (0.1.0:D0018: any of them rebuilds everything)."""
    before = old.environment.fingerprints if old is not None else {}
    after = built.environment.fingerprints
    details = [
        f"{_label(name)} {before.get(name, 'absent')} -> {after.get(name, 'absent')}"
        for name in sorted(set(before) | set(after))
        if before.get(name) != after.get(name)
    ]
    if (
        old is not None
        and old.environment.providers != built.environment.providers_digest
    ):
        details.append(
            "the provider set changed (a provider was added, removed or moved)"
        )
    return "; ".join(details) or "the provider set or a fingerprint changed"


def _label(name: str) -> str:
    kind, _, rest = name.partition(":")
    labels = {
        "model": "model override of kind",
        "code": "code",
        "schema": "model schema of kind",
    }
    return f"{labels[kind]} {rest}" if rest and kind in labels else f"provider {name}"


def _explain_config(old: Lock | None, built: Plan) -> str:
    """Name CLI overrides (0.1.0:D0034) when they differ between the lock and this run."""
    before = old.cli_overrides if old is not None else {}
    after = built.cli_overrides
    changed = sorted(
        k for k in set(before) | set(after) if before.get(k) != after.get(k)
    )
    if not changed:
        return "config/chancellor changed"
    details = [
        (
            f"{key} {before[key]!r} (lock) -> {after[key]!r}"
            if key in before and key in after
            else (
                f"{key}={before[key]!r} in the lock, none now"
                if key in before
                else f"{key}={after[key]!r} now, none in the lock"
            )
        )
        for key in changed
    ]
    return "config/chancellor changed: CLI override " + "; ".join(details)


__all__ = ["BuildResult", "PlannedDocument", "explain", "plan", "run"]
