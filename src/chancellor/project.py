"""A loaded project: root, configuration, registry and validated records.

`Project.load` runs the whole load in order: find the data file and the root, bootstrap,
load providers and build the registry, merge the data files, validate the configuration,
validate every kind's section through the model hooks, index the records and resolve refs.
Every failure maps onto an exit code through its error class.
"""

import logging
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, get_args

from pydantic import BaseModel, ValidationError

from .api import (
    ChancellorConfig,
    ConfigLoader,
    ConfigTree,
    CoreModel,
    Degradation,
    FormatContext,
    Formatter,
    Linter,
    LoadedConfig,
    LoaderContext,
    MetaInfo,
    Model,
    Origin,
    ProjectModel,
    RootModel,
)
from .api import Version as VersionMarker
from .api import VersionScheme, collect_ref_links, section_types
from .canonical import digest_of
from .codeload import load_object, model_fingerprint, reset_source_digests
from .config import Bootstrap, DataTreeLoader, bootstrap, flatten, load_config
from .datatree import DataTree, check_scoped, location_for, merge_kind_data, read_tree
from .errors import ChancellorError, ConfigError, InputError, location_text, violations
from .keys import ModuleKeys
from .paths import (
    confine,
    find_data_file,
    find_root,
    output_path_for,
    relative,
    template_suffix,
)
from .providers import builtin_providers, local_providers, plugin_providers
from .registry import Registry
from .versions import SCHEME_ALIASES, absolute_id, split_absolute
from .yamlio import load as load_yaml

logger = logging.getLogger(__name__)

REFERENCE_LOGGER = logging.getLogger("chancellor.references")
"""Warns about historic references, on stderr even without `-v`."""


@dataclass
class Section:
    """A kind's validated data: its core document (indexed) and its records by ID."""

    kind: str
    core: CoreModel | None
    records: list[Model]

    def documents(self) -> list[tuple[str, Model]]:
        """(part, record) for the core document, if any, then the records."""
        result: list[tuple[str, Model]] = []
        if self.core is not None:
            result.append(("core_document", self.core))
        result.extend(("records", record) for record in self.records)
        return result


@dataclass(frozen=True)
class RootModelInfo:
    """A supplied root model and its fingerprint (0.1.0:D0030)."""

    reference: str
    model: type[BaseModel]
    origin: str
    fingerprint: str


@dataclass(frozen=True)
class ModelOverride:
    """A config model override of one kind (`kinds.<kind>.model` / `core_model`)."""

    kind: str
    references: tuple[str, ...]
    origins: tuple[str, ...]
    fingerprint: str


@dataclass
class Project:
    """Everything a command needs about the project."""

    root: Path
    keys: ModuleKeys
    registry: Registry
    config: Any
    config_digest: str
    data_file: Path | None = None
    tree: DataTree | None = None
    sections: dict[str, Section] = field(default_factory=dict)
    records: dict[str, tuple[str, Model]] = field(default_factory=dict)
    root_model: RootModelInfo | None = None
    model_overrides: dict[str, ModelOverride] = field(default_factory=dict)
    code_fingerprints: dict[str, str] = field(default_factory=dict)
    code_degradations: list[Degradation] = field(default_factory=list)
    version_scheme: VersionScheme | None = None
    """The configured version scheme (0.1.0:D0036)."""
    historic_refs: list[tuple[str, str, str]] = field(default_factory=list)
    """(kind, record ID, reference) of every reference into an older record-set version."""
    record_set_version: str | None = None
    """`meta/<key>/version`: the version of the record set as a whole (0.1.0:D0036)."""
    cli_overrides: dict[str, Any] = field(default_factory=dict)
    """`--set` values this load applied, by dotted key (0.1.0:D0034)."""
    degradations: list[Degradation] = field(default_factory=list)

    @classmethod
    def load(
        cls,
        data_file: Path | None = None,
        *,
        start: Path | None = None,
        keys: ModuleKeys | None = None,
        require_data: bool = True,
        overrides: Mapping[str, Any] | None = None,
    ) -> "Project":
        """Load the project; without a data file, built-in defaults apply unless required."""
        keys = keys or ModuleKeys()
        reset_source_digests()
        found = find_data_file(data_file, start)
        if found is None:
            if require_data:
                raise ConfigError(
                    "No chancellor.yaml found in this folder or above; pass --data or set "
                    "CHANCELLOR_DATA"
                )
            return cls._defaults(start or Path.cwd(), keys, overrides)
        root = find_root(found)
        where = relative(root, found)
        main = check_scoped(load_yaml(found, error=ConfigError), where, keys)
        boot = bootstrap(main, keys, where)
        providers = [*builtin_providers(), *plugin_providers()]
        providers += local_providers([p.model_dump() for p in boot.providers], root)
        registry = Registry.build(providers)
        tree = read_tree(root, found, main, boot.include, keys)
        _check_bootstrap_unchanged(tree, boot, keys)
        root_model, root_degradations = _load_root_model(root, boot, keys)
        settings, config_digest, loader_degradations, loader_codes = _configure(
            registry, tree, boot, (root, found, keys), root_model, overrides
        )
        raw_kinds = tree.module("config", keys.config).get("kinds") or {}
        registry = registry.configured(settings.kinds.model_dump())
        project = cls(
            root=root,
            keys=keys,
            registry=registry,
            config=settings,
            config_digest=config_digest,
            data_file=found,
            tree=tree,
            root_model=root_model,
        )
        project.record_set_version = _record_set_version(tree, keys)
        project.code_degradations.extend(root_degradations)
        project.code_degradations.extend(loader_degradations)
        project.code_fingerprints.update(loader_codes)
        project.cli_overrides = flatten(overrides or {})
        project._check_root_sections()
        project._apply_model_overrides(raw_kinds)
        project.version_scheme = project.scheme()
        project._validate_sections()
        project._index()
        project.formatter()  # resolve and fingerprint it now; a bad type fails the load
        project.degradations = [
            *registry.all_degradations(),
            *project.code_degradations,
        ]
        return project

    @classmethod
    def _defaults(
        cls, root: Path, keys: ModuleKeys, overrides: Mapping[str, Any] | None = None
    ) -> "Project":
        registry = Registry.build([*builtin_providers(), *plugin_providers()])
        context = LoaderContext(root=root.resolve(), data_file=None, keys=keys, tree={})
        loaded = [DataTreeLoader(context).load()]
        settings, config_digest = load_config(
            registry, loaded, keys, overrides=overrides
        )
        _log_overrides(overrides)
        project = cls(
            root=root.resolve(),
            keys=keys,
            registry=registry,
            config=settings,
            config_digest=config_digest,
        )
        project.cli_overrides = flatten(overrides or {})
        project.version_scheme = project.scheme()
        project.degradations = registry.all_degradations()
        return project

    # Formatting

    def type_class(self, point: str, address: str, setting: str | None = None) -> type:
        """The class of a formatter, linter or version-scheme type: a registered address such
        as `builtin.mdformat`, or an import path `path/to/file.py:Class` / `module:Class`
        (0.1.0:D0009), whose code fingerprint is recorded under `code:<address>`."""
        if ":" not in address:
            return self.registry.type_for(point, address)
        setting = setting or f"config.{self.keys.config}.{point[:-1]}.type"
        loaded = load_object(self.root, address, setting)
        base = {
            "formatters": Formatter,
            "linters": Linter,
            "version_schemes": VersionScheme,
        }[point]
        if not (isinstance(loaded.obj, type) and issubclass(loaded.obj, base)):
            raise ConfigError(f"{setting}: {address} is not a {base.__name__} subclass")
        self.code_fingerprints[f"code:{address}"] = loaded.code
        self.code_degradations.extend(loaded.degradations)
        return loaded.obj

    def scheme(self) -> VersionScheme:
        """The configured version scheme: a built-in short name (`semver`, `pep440`, `free`),
        a type address, or an import path."""
        name = self.config.versioning.scheme
        scheme_type = self.type_class(
            "version_schemes",
            SCHEME_ALIASES.get(name, name),
            f"config.{self.keys.config}.versioning.scheme",
        )
        return scheme_type()

    def formatter(self) -> Formatter:
        """The configured formatter, its arguments validated by its own type."""
        ref = self.config.formatter
        formatter_type = self.type_class("formatters", ref.type)
        try:
            return formatter_type(**ref.arguments())
        except ValidationError as exc:
            raise ConfigError(
                "\n".join(
                    [f"Invalid arguments for formatter {ref.type}:", *violations(exc)]
                )
            ) from exc

    def format_context(self) -> FormatContext:
        return FormatContext(wrap_width=self.config.wrap_width)

    # Loading steps

    def _check_root_sections(self) -> None:
        """A supplied `ProjectModel`'s sections must name registered kinds and type them with
        subclasses of the providers' models, so the providers' templates keep working.
        """
        if self.root_model is None or not issubclass(
            self.root_model.model, ProjectModel
        ):
            return
        for kind, section in self.root_model.model.section_fields().items():
            where = f"data_model {self.root_model.reference}, field {kind}"
            if kind not in self.registry.kinds:
                raise ConfigError(f"{where}: {kind} is not a registered kind")
            spec = self.registry.kinds[kind]
            core_type, record_type = section_types(section)
            if isinstance(record_type, type) and not issubclass(
                record_type, spec.model
            ):
                raise ConfigError(
                    f"{where}: records of {record_type.__name__} are not a subclass of "
                    f"{spec.model.__module__}.{spec.model.__name__}"
                )
            core_ok = (
                spec.core_model is None
                or not isinstance(core_type, type)
                or core_type is CoreModel
                or issubclass(core_type, spec.core_model)
            )
            if not core_ok:
                raise ConfigError(
                    f"{where}: core {core_type.__name__} is not a subclass of "
                    f"{spec.core_model.__module__}.{spec.core_model.__name__}"
                )

    def root_declared_kinds(self) -> set[str]:
        """Kinds a supplied root model validates: its sections, or every kind for a model
        that does not inherit `ProjectModel` (its sections cannot be known in advance).
        """
        if self.root_model is None:
            return set()
        if issubclass(self.root_model.model, ProjectModel):
            return set(self.root_model.model.section_fields())
        return set(self.registry.kinds)

    def _apply_model_overrides(self, raw_kinds: Mapping[str, Any]) -> None:
        """Replace kinds' models by consumer subclasses named in config (0.1.0:D0025)."""
        prefix = f"config.{self.keys.config}.kinds"
        for kind, settings in sorted(self.config.kinds.model_dump().items()):
            references = {
                part: settings.get(part)
                for part in ("model", "core_model")
                if settings.get(part)
            }
            if not references:
                continue
            sites = {
                part: f"{prefix}.{kind}.{part}" for part in ("model", "core_model")
            }
            if kind in self.root_declared_kinds():
                raise ConfigError(
                    f"config.{self.keys.config}.data_model and {sites[next(iter(references))]} "
                    "both say which model validates the data; use one of them"
                )
            loaded = {
                part: load_object(self.root, reference, sites[part])
                for part, reference in references.items()
            }
            code = digest_of({part: obj.code for part, obj in sorted(loaded.items())})
            for obj in loaded.values():
                self.code_degradations.extend(obj.degradations)
            self.registry = self.registry.with_models(
                kind,
                model=loaded["model"].obj if "model" in loaded else None,
                core_model=loaded["core_model"].obj if "core_model" in loaded else None,
                code=code,
                sites=sites,
            )
            spec = self.registry.kinds[kind]
            models = [spec.model] + ([spec.core_model] if spec.core_model else [])
            self.model_overrides[kind] = ModelOverride(
                kind=kind,
                references=tuple(obj.reference for obj in loaded.values()),
                origins=tuple(obj.origin for obj in loaded.values()),
                fingerprint=model_fingerprint(models, code),
            )
        del raw_kinds

    def _validate_sections(self) -> None:
        assert self.tree is not None
        raw_sections = {
            name: value
            for name, value in self.tree.sections().items()
            if name in self.registry.kinds
        }
        for name in sorted(self.tree.sections()):
            files = ", ".join(self.tree.section_origins.get(name, [])) or "-"
            if name in self.registry.kinds:
                logger.info(
                    "section %s: kind of provider %s (from %s)",
                    name,
                    self.registry.kinds[name].provider,
                    files,
                )
            else:
                logger.info(
                    "section %s: no registered kind, ignored (from %s; kinds: %s)",
                    name,
                    files,
                    ", ".join(sorted(self.registry.kinds)),
                )
        declared = self.root_declared_kinds()
        if self.root_model is not None:
            self._sections_from_root_model(
                {k: v for k, v in raw_sections.items() if k in declared}
            )
        # Kinds a supplied root model does not declare take the generated path.
        problems: list[str] = []
        for name, raw in sorted(raw_sections.items()):
            if name in declared:
                continue
            try:
                self.sections[name] = self._section(name, raw)
            except InputError as exc:
                problems.append(str(exc))
        if problems:
            raise InputError("\n".join(problems))

    def _section(self, name: str, raw: Any) -> Section:
        spec = self.registry.kinds[name]
        if not isinstance(raw, dict):
            raise InputError(f"Invalid {name} input:\n- {name}: must be a mapping")
        loaded = dict(raw)
        if spec.core_model is not None and "core" in loaded:
            loaded["core"] = spec.core_model.model_load(
                loaded["core"], origin=self._origin(name, loaded["core"])
            )
        records = loaded.get("records")
        if isinstance(records, list):
            loaded["records"] = [
                spec.model.model_load(item, origin=self._origin(name, item))
                for item in records
            ]
        model = self.registry.section_model(name)
        try:
            validated = model.model_validate(loaded)
        except ValidationError as exc:
            raise InputError.from_validation(exc, name, prefix=name) from exc
        return self._indexed_section(
            name, getattr(validated, "core", None), validated.records
        )

    def _origin(self, name: str, item: Any) -> Origin:
        assert self.tree is not None
        record_id = item.get("id") if isinstance(item, dict) else None
        file = self.tree.record_origins.get((name, str(record_id)), self.tree.files[0])
        return Origin(file=file, location=f"{name}.{record_id}")

    def _sections_from_root_model(self, raw_sections: dict[str, Any]) -> None:
        assert self.root_model is not None
        model = self.root_model.model
        if issubclass(model, ProjectModel):
            instance = self._validate_project_model(model)
        else:
            try:
                instance = model.model_validate(raw_sections)
            except ValidationError as exc:
                raise InputError.from_validation(exc, model) from exc
        if isinstance(instance, RootModel):
            pairs = dict(instance.chancellor_sections())
        else:
            pairs = {}
            for name in self.registry.kinds:
                section = getattr(instance, name, None)
                if section is not None:
                    pairs[name] = (
                        getattr(section, "core", None),
                        list(section.records),
                    )
        for name, (core, records) in pairs.items():
            if name not in self.registry.kinds:
                raise ConfigError(
                    f"data_model: section {name} is not a registered kind"
                )
            for item in [core, *records]:
                if item is not None and not isinstance(item, Model):
                    raise ConfigError(
                        f"data_model: {name} holds {type(item).__name__}, not a chancellor Model"
                    )
            ordered = sorted(records, key=lambda record: record.id)
            self.sections[name] = self._indexed_section(name, core, ordered)

    def _validate_project_model(self, model: type[ProjectModel]) -> ProjectModel:
        """Validate the whole tree, `_api` and `config` included, with the merged configuration
        in place of the raw one, so environment overrides and defaults count. Errors under
        `_api` or `config` are configuration errors; under a record section, input errors.
        """
        assert self.tree is not None
        data = deepcopy(self.tree.data)
        data.setdefault("config", {})[self.keys.config] = self.config.model_dump(
            mode="json"
        )
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            facets = [
                e
                for e in exc.errors()
                if e["loc"] and e["loc"][0] in ("_api", "config", "api")
            ]
            name = model.__name__
            if facets:
                lines = [f"Invalid {name} configuration:"]
                lines += [f"- {location_text(e['loc'])}: {e['msg']}" for e in facets]
                raise ConfigError("\n".join(lines)) from exc
            raise InputError.from_validation(exc, model) from exc

    def _indexed_section(
        self, name: str, core: Any, records: Sequence[Model]
    ) -> Section:
        suffix = template_suffix(self.registry.kinds[name].templates.records)
        indexed = (
            core.index_records(records, suffix=suffix)
            if isinstance(core, CoreModel)
            else None
        )
        return Section(kind=name, core=indexed, records=list(records))

    def _index(self) -> None:
        problems: list[str] = []
        for name, section in sorted(self.sections.items()):
            for _, record in section.documents():
                if record.id in self.records:
                    other = self.records[record.id][0]
                    problems.append(
                        f"- {record.id} is defined in {other} and in {name}"
                    )
                    continue
                self.records[record.id] = (name, record)
        for record_id, (name, record) in sorted(self.records.items()):
            for ref in record.model_index().refs:
                kind_of = self.classify_ref(ref)
                if kind_of is None:
                    continue  # external identifier
                bare, version, state = kind_of
                where = f"- {name}.{record_id}: reference {ref}"
                if state == "newer":
                    problems.append(
                        f"{where} names record-set version {version}, newer than the data "
                        f"({self.record_set_version})"
                    )
                elif state == "historic":
                    # Not resolvable against current data, so not dangling (0.1.0:D0036).
                    self.historic_refs.append((name, record_id, ref))
                    REFERENCE_LOGGER.warning(
                        "historic reference %s in %s.%s: the record set is version %s",
                        ref,
                        name,
                        record_id,
                        self.record_set_version or "(none set)",
                    )
                elif bare not in self.records:
                    problems.append(f"{where} names no record")
        if problems:
            raise InputError(
                "\n".join(
                    [
                        "Invalid record references:",
                        *problems,
                        "A value shaped like a record ID must name a record. Write an external "
                        "reference so it cannot be mistaken for one: "
                        "<project>:<version>:<id> (other-project:1.0.0:D0001) or a URL.",
                    ]
                )
            )
        self._validate_versions()

    def id_shaped(self, value: str) -> bool:
        """Whether `value` looks like an ID of a registered kind."""
        return any(
            spec.id_pattern is not None and spec.id_pattern.fullmatch(value)
            for spec in self.registry.kinds.values()
        )

    def _validate_versions(self) -> None:
        """Under a scheme other than `free`: the record-set version and every `Version`
        field parse, and versions in a list of models increase, oldest first (0.1.0:D0036).
        """
        scheme = self.version_scheme
        if scheme is None or not scheme.checks:
            return
        name = self.config.versioning.scheme
        problems: list[str] = []
        if self.record_set_version is not None and not scheme.is_version(
            self.record_set_version
        ):
            problems.append(
                f"- meta.{self.keys.meta}.version: {self.record_set_version!r} is not a valid "
                f"{name} version"
            )
        for record_id, (kind, record) in sorted(self.records.items()):
            problems.extend(
                _version_problems(record, scheme, f"{kind}.{record_id}", name)
            )
        if problems:
            raise InputError("\n".join(["Invalid versions:", *problems]))

    def absolute_id(self, record_id: str) -> str | None:
        """A record's absolute ID, `None` while the record set has no version (0.1.0:D0036)."""
        return absolute_id(
            self.record_set_version, record_id, self.config.versioning.absolute_id
        )

    def classify_ref(self, value: str) -> tuple[str, str | None, str] | None:
        """(bare ID, version, state) of a reference value, or `None` for an external one.

        State: `bare` (an ID alone, meaning the current version), `current` (an absolute ID
        of the current version), `historic` (an older version, or any other version when the
        scheme does not order versions or the record set has none), `newer`.
        """
        scheme = self.version_scheme
        if scheme is not None:
            absolute = split_absolute(value, self.config.versioning.absolute_id, scheme)
            if absolute is not None and self.id_shaped(absolute[1]):
                version, bare = absolute
                if version == self.record_set_version:
                    return bare, version, "current"
                current = self.record_set_version
                if scheme.checks and current is not None and scheme.is_version(current):
                    if scheme.compare(version, current) > 0:
                        return bare, version, "newer"
                return bare, version, "historic"
        return (value, None, "bare") if self.id_shaped(value) else None

    def resolve_id(self, text: str) -> str:
        """A record ID given on the command line, bare or absolute. An older version is a
        historic reference: a warning, then the current record of that ID, if it exists.
        """
        kind_of = self.classify_ref(text)
        if kind_of is None or kind_of[2] in ("bare", "current"):
            return kind_of[0] if kind_of else text
        bare, version, state = kind_of
        if state == "newer":
            raise InputError(
                f"{text} names record-set version {version}, newer than the data "
                f"({self.record_set_version})"
            )
        if bare not in self.records:
            raise InputError(f"historic reference to {text}: {bare} does not exist now")
        REFERENCE_LOGGER.warning(
            "historic reference to %s; showing the current %s", text, bare
        )
        return bare

    def ref_context(self, record: Model) -> dict[str, list[dict[str, Any]]]:
        """What a record's templates see of other records, under `refs.<field>` (0.1.0:D0032).

        Per reference, exactly what its `depends` declares: `{id}`; `{id, file_name, path}`;
        or `{id, file_name, path, data}`. Targets outside the project (external identifiers)
        appear with their ID only. The `refs` digest part covers this mapping, so a template
        cannot read anything of another record that the digest does not see.
        """
        context: dict[str, list[dict[str, Any]]] = {}
        for link in collect_ref_links(record):
            kind_of = self.classify_ref(link.id)
            if kind_of is None:  # external
                context.setdefault(link.field, []).append(
                    {"id": link.id, "historic": False}
                )
                continue
            bare, version, state = kind_of
            entry: dict[str, Any] = {
                "id": bare,
                "ref": link.id,
                "version": version or self.record_set_version,
                "historic": state == "historic",
                "current": None,
            }
            target = self.records.get(bare)
            if state == "historic":
                # A historic reference reads nothing of the old record; the current record of
                # that ID, if any, is offered for linking.
                if target is not None:
                    path = self.document_path(*target)
                    entry["current"] = {
                        "id": bare,
                        "file_name": path.name,
                        "path": relative(self.root, path),
                        "absolute_id": self.absolute_id(bare),
                    }
            elif target is not None and link.depends in ("name", "data"):
                path = self.document_path(*target)
                entry["file_name"] = path.name
                entry["path"] = relative(self.root, path)
                entry["absolute_id"] = self.absolute_id(bare)
                if link.depends == "data":
                    # chains (deferred, 0.1.0:D0033): would follow the target's own depends="data"
                    # edges here, with a cycle guard, nesting their `refs` into the entry; the
                    # closure then enters the refs digest through this context.
                    entry["data"] = target[1].model_serialize()
            context.setdefault(link.field, []).append(entry)
        return context

    def template_extras(self, record: Model) -> dict[str, Any]:
        """What templates see besides the record's data and references: the record set's
        version and the record's absolute ID (0.1.0:D0036). Covered by the `meta` digest part.
        """
        return {
            "meta": {"version": self.record_set_version},
            "absolute_id": self.absolute_id(record.id),
        }

    def document_path(self, kind: str, record: Model) -> Path:
        """Output path of a record's document, by the kind's template for its part."""
        spec = self.registry.kinds[kind]
        section = self.sections.get(kind)
        part = (
            "core_document"
            if section is not None and section.core is record
            else "records"
        )
        return output_path_for(self.root, spec.folder, record, spec.template(part))

    def resolved_refs(self, record: Model) -> list[str]:
        """IDs of current records `record` references: bare IDs and absolute IDs of the
        current version; historic references are left out."""
        found = []
        for ref in record.model_index().refs:
            kind_of = self.classify_ref(ref)
            if kind_of is not None and kind_of[2] in ("bare", "current"):
                if kind_of[0] in self.records:
                    found.append(kind_of[0])
        return found

    def kind_folder(self, kind: str) -> Path:
        return confine(
            self.root, self.registry.kinds[kind].folder, setting=f"kinds.{kind}.folder"
        )


def _configure(
    registry: Registry,
    tree: DataTree,
    boot: Bootstrap,
    where: tuple[Path, Path, ModuleKeys],
    root_model: "RootModelInfo | None",
    overrides: Mapping[str, Any] | None,
) -> tuple[Any, str, list[Degradation], dict[str, str]]:
    """Phase two: run the loaders, validate the merged configuration (on top of a supplied
    root model's `ChancellorConfig` subclass), then merge per-kind data files (0.1.0:D0019).
    """
    root, data_file, keys = where
    context = LoaderContext(
        root=root,
        data_file=data_file,
        keys=keys,
        tree=tree.data,
        files=tuple(tree.files),
    )
    loaded, degradations, fingerprints = _run_loaders(registry, boot.loaders, context)
    settings, digest = load_config(
        registry,
        loaded,
        keys,
        config_class(root_model.model if root_model else None, keys),
        overrides,
    )
    _log_overrides(overrides)
    for kind, kind_config in sorted(settings.kinds):
        location = location_for(kind_config)
        if location is not None:
            merge_kind_data(tree, root, kind, location)
    return settings, digest, degradations, fingerprints


def _version_problems(
    instance: BaseModel, scheme: VersionScheme, where: str, name: str
) -> list[str]:
    """Problems with `Version` fields in `instance`, nested models and lists included."""
    problems: list[str] = []
    for field_name, info in type(instance).model_fields.items():
        value = getattr(instance, field_name)
        here = f"{where}.{field_name}"
        if any(isinstance(item, VersionMarker) for item in info.metadata):
            if isinstance(value, str) and not scheme.is_version(value):
                problems.append(f"- {here}: {value!r} is not a valid {name} version")
        elif isinstance(value, BaseModel):
            problems.extend(_version_problems(value, scheme, here, name))
        elif (
            isinstance(value, list)
            and value
            and all(isinstance(v, BaseModel) for v in value)
        ):
            for index, item in enumerate(value):
                problems.extend(
                    _version_problems(item, scheme, f"{here}[{index}]", name)
                )
            problems.extend(_ordering_problems(value, scheme, here))
    return problems


def _ordering_problems(
    items: list[BaseModel], scheme: VersionScheme, where: str
) -> list[str]:
    """Versions in a list of models must increase in list order."""
    marked = [
        field_name
        for field_name, info in type(items[0]).model_fields.items()
        if any(isinstance(item, VersionMarker) for item in info.metadata)
    ]
    problems = []
    for field_name in marked:
        values = [getattr(item, field_name) for item in items]
        if not all(isinstance(v, str) and scheme.is_version(v) for v in values):
            continue  # already reported as unparsable
        for index in range(1, len(values)):
            if scheme.compare(values[index - 1], values[index]) >= 0:
                problems.append(
                    f"- {where}[{index}].{field_name}: {values[index]!r} does not increase "
                    f"over {values[index - 1]!r}"
                )
    return problems


def _record_set_version(tree: DataTree, keys: ModuleKeys) -> str | None:
    """The record-set version from `meta/<key>`, validated as record data."""
    raw = tree.module("meta", keys.meta)
    try:
        return MetaInfo.model_validate(raw).version
    except ValidationError as exc:
        raise InputError.from_validation(
            exc, MetaInfo, prefix=f"meta.{keys.meta}"
        ) from exc


def _run_loaders(
    registry: Registry, entries: Sequence[Any], context: LoaderContext
) -> tuple[list[LoadedConfig], list[Degradation], dict[str, str]]:
    """Construct and run the configured loaders, highest priority first (0.1.0:D0034). Each entry is
    a type address or import path, or a mapping with `type` and the loader's arguments.
    """
    loaded: list[LoadedConfig] = []
    degradations: list[Degradation] = []
    fingerprints: dict[str, str] = {}
    for index, entry in enumerate(entries):
        site = f"config.{context.keys.config}.loaders[{index}]"
        address, arguments = (
            (entry, {})
            if isinstance(entry, str)
            else (entry.get("type"), {k: v for k, v in entry.items() if k != "type"})
        )
        if not isinstance(address, str) or not address:
            raise ConfigError(f"{site}: name a loader type, e.g. builtin.data_file")
        if ":" in address:
            code = load_object(context.root, address, site)
            loader_type = code.obj
            degradations.extend(code.degradations)
            fingerprints[f"code:{address}"] = code.code
        else:
            loader_type = registry.type_for("config_loaders", address)
        if not (
            isinstance(loader_type, type) and issubclass(loader_type, ConfigLoader)
        ):
            raise ConfigError(f"{site}: {address} is not a ConfigLoader subclass")
        try:
            loaded.append(loader_type(context, **arguments).load())
        except ChancellorError:
            raise
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ConfigError(f"{site}: loader {address} failed: {exc}") from exc
    return loaded, degradations, fingerprints


OVERRIDE_LOGGER = logging.getLogger("chancellor.overrides")
"""Logs every `--set` value applied; the CLI shows it at INFO whenever `--set` is used."""


def _log_overrides(overrides: Mapping[str, Any] | None) -> None:
    for key, value in sorted(flatten(overrides or {}).items()):
        OVERRIDE_LOGGER.info("CLI override %s = %r", key, value)


def _load_root_model(
    root: Path, boot: Bootstrap, keys: ModuleKeys
) -> tuple["RootModelInfo | None", list[Degradation]]:
    """The supplied root model (`data_model`), loaded before configuration (0.1.0:D0030), because a
    `ProjectModel` subclass may bring its own `ChancellorConfig` subclass."""
    if boot.data_model is None:
        return None, []
    setting = f"config.{keys.config}.data_model"
    loaded = load_object(root, boot.data_model, setting)
    model = loaded.obj
    if not (isinstance(model, type) and issubclass(model, BaseModel)):
        raise ConfigError(f"{setting}: {boot.data_model} is not a Pydantic model")
    if not issubclass(model, ProjectModel):
        logger.info(
            "data_model %s does not inherit chancellor.api.ProjectModel: its record sections "
            "are validated, configuration is not composed from it",
            boot.data_model,
        )
    info = RootModelInfo(
        reference=boot.data_model,
        model=model,
        origin=loaded.origin,
        fingerprint=model_fingerprint([model], loaded.code),
    )
    return info, list(loaded.degradations)


def config_class(
    model: type[BaseModel] | None, keys: ModuleKeys
) -> type[ChancellorConfig]:
    """The `ChancellorConfig` subclass a root model declares under `config/<key>`, if any."""
    if model is None or not issubclass(model, ProjectModel):
        return ChancellorConfig
    tree = _class_in(model.model_fields["config"].annotation, ConfigTree)
    if tree is None:
        return ChancellorConfig
    for name, info in tree.model_fields.items():
        if (info.alias or name) == keys.config:
            found = _class_in(info.annotation, ChancellorConfig)
            if found is not None:
                return found
    return ChancellorConfig


def _class_in(annotation: Any, base: type) -> Any:
    if isinstance(annotation, type) and issubclass(annotation, base):
        return annotation
    for argument in get_args(annotation):
        found = _class_in(argument, base)
        if found is not None:
            return found
    return None


def _check_bootstrap_unchanged(
    tree: DataTree, boot: Bootstrap, keys: ModuleKeys
) -> None:
    """Bootstrap keys belong in the main data file, read before anything else: the merged tree
    must say exactly what the main file says about them."""
    del boot
    main = tree.raw[0][1] if tree.raw else {}

    def config_of(data: dict[str, Any], key: str) -> dict[str, Any]:
        value = (data.get("config") or {}).get(key) or {}
        return value if isinstance(value, dict) else {}

    sites = [(keys.providers, "providers")] + [
        (keys.config, name) for name in ("include", "loaders", "data_model")
    ]
    moved = [
        f"config.{key}.{name}"
        for key, name in sites
        if config_of(tree.data, key).get(name) != config_of(main, key).get(name)
    ]
    if moved:
        raise ConfigError(
            f"{', '.join(moved)} must be set in the main data file, not in included files"
        )
