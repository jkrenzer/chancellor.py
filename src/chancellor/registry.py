"""The registry: the only lookup path from a kind to its provider, models, templates and
folder, and from a type address to its class.

Providers load in a fixed, reported order: built-in, plugins by distribution name, local
providers in declared order. A later provider may add a kind or a template but may not
redefine one; an intended override is written out in config as a template address such as
`project/decision.md.j2`.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from importlib.resources.abc import Traversable
from typing import Any, Literal

from jinja2 import Environment, TemplateNotFound
from pydantic import BaseModel, Field, create_model

from .api import (
    ConfigLoader,
    CoreModel,
    Degradation,
    Formatter,
    KindTemplates,
    Linter,
    Model,
    ProjectModel,
    Provider,
    Section,
    VersionScheme,
)
from .canonical import digest_of
from .errors import ConfigError
from .providers import declarative_model
from .templating import TraversableLoader, make_environment, template_closure

Part = Literal["records", "core_document"]

_TYPE_BASES: dict[str, type] = {
    "formatters": Formatter,
    "linters": Linter,
    "config_loaders": ConfigLoader,
    "version_schemes": VersionScheme,
}


@dataclass(frozen=True)
class KindSpec:
    """Everything chancellor knows about one record kind."""

    name: str
    provider: str
    folder: str
    templates: KindTemplates
    model: type[Model]
    core_model: type[CoreModel] | None
    aliases: Mapping[str, Part] = field(default_factory=dict)
    model_code: str | None = None
    """Code fingerprint of a config model override; `None` when the provider's models apply."""

    def template(self, part: Part) -> str:
        name = (
            self.templates.records
            if part == "records"
            else self.templates.core_document
        )
        if name is None:
            raise ConfigError(f"Kind {self.name} has no core document")
        return name

    def model_for(self, part: Part) -> type[Model]:
        if part == "records":
            return self.model
        if self.core_model is None:
            raise ConfigError(f"Kind {self.name} has no core document")
        return self.core_model

    @property
    def id_pattern(self) -> re.Pattern[str] | None:
        """Pattern of the kind's record IDs, if its model declares one."""
        schema = self.model.model_json_schema()
        pattern = schema.get("properties", {}).get("id", {}).get("pattern")
        return re.compile(pattern) if pattern else None


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[-_.]", name) if part)


@dataclass
class Registry:
    """Resolved contributions of the loaded providers."""

    providers: list[Provider]
    kinds: dict[str, KindSpec]
    types: dict[tuple[str, str], type]
    environment: Environment
    template_providers: dict[str, Traversable]
    degradations: list[Degradation] = field(default_factory=list)
    _closures: dict[str, tuple[dict[str, str], bool]] = field(
        default_factory=dict, repr=False
    )

    @classmethod
    def build(cls, providers: Sequence[Provider]) -> "Registry":
        """Resolve providers in load order; a name or kind defined twice is an error."""
        seen: dict[str, Provider] = {}
        kinds: dict[str, KindSpec] = {}
        aliases: dict[str, str] = {}
        types: dict[tuple[str, str], type] = {}
        roots: dict[str, Traversable] = {}
        for provider in providers:
            if provider.name in seen:
                raise ConfigError(
                    f"Provider {provider.name} is loaded twice: from "
                    f"{seen[provider.name].origin} and from {provider.origin}"
                )
            seen[provider.name] = provider
            root = provider.template_root()
            if root is not None:
                roots[provider.name] = root
            for kind_name, decl in provider.manifest.kinds.items():
                if kind_name in kinds:
                    raise ConfigError(
                        f"Kind {kind_name} from provider {provider.name} is already defined by "
                        f"{kinds[kind_name].provider}; a provider may add kinds, not redefine "
                        "them"
                    )
                spec = _kind_spec(provider, kind_name, decl)
                for alias in [kind_name, *spec.aliases]:
                    if alias in aliases:
                        raise ConfigError(
                            f"Name {alias} of kind {kind_name} is already used by kind "
                            f"{aliases[alias]}"
                        )
                    aliases[alias] = kind_name
                kinds[kind_name] = spec
            for point, base in _TYPE_BASES.items():
                for type_name, reference in getattr(provider.manifest, point).items():
                    address = f"{provider.name}.{type_name}"
                    loaded = provider.import_object(reference)
                    if not (isinstance(loaded, type) and issubclass(loaded, base)):
                        raise ConfigError(
                            f"{point} {address}: {reference} is not a {base.__name__} subclass"
                        )
                    types[(point, address)] = loaded
        registry = cls(
            providers=list(providers),
            kinds=kinds,
            types=types,
            environment=make_environment(roots),
            template_providers=roots,
        )
        for spec in kinds.values():
            registry.check_templates(spec)
        return registry

    # Lookups

    def lookup(self, name: str) -> tuple[KindSpec, Part]:
        """A kind and document part by kind name or alias, such as `decisions` or `adr-core`."""
        if name in self.kinds:
            return self.kinds[name], "records"
        for spec in self.kinds.values():
            if name in spec.aliases:
                return spec, spec.aliases[name]
        raise ConfigError(f"Unknown kind {name}; known: {', '.join(self.names())}")

    def names(self) -> list[str]:
        """Every kind name and alias."""
        return [n for spec in self.kinds.values() for n in (spec.name, *spec.aliases)]

    def type_for(self, point: str, address: str) -> type:
        """The class registered as `address` (e.g. `builtin.mdformat`) for an extension point."""
        try:
            return self.types[(point, address)]
        except KeyError:
            known = sorted(a for p, a in self.types if p == point)
            raise ConfigError(
                f"Unknown {point[:-1].replace('_', ' ')} type {address}; available: "
                f"{', '.join(known) or 'none'} (providers: {', '.join(self.provider_names())})"
            ) from None

    def provider(self, name: str) -> Provider:
        for provider in self.providers:
            if provider.name == name:
                return provider
        raise ConfigError(f"Unknown provider {name}")

    def provider_names(self) -> list[str]:
        return [provider.name for provider in self.providers]

    # Templates

    def check_templates(self, spec: KindSpec) -> None:
        for name in (spec.templates.records, spec.templates.core_document):
            if name is not None:
                self.template_source(name, setting=f"kind {spec.name}")

    def template_source(self, name: str, *, setting: str = "template") -> str:
        prefix = name.partition("/")[0]
        if prefix not in self.template_providers:
            raise ConfigError(
                f"{setting}: template {name} names no provider with templates; known "
                f"prefixes: {', '.join(sorted(self.template_providers)) or 'none'}"
            )
        try:
            assert self.environment.loader is not None
            return self.environment.loader.get_source(self.environment, name)[0]
        except TemplateNotFound as exc:
            raise ConfigError(f"{setting}: template {name} not found") from exc

    def template_closure(self, name: str) -> tuple[dict[str, str], bool]:
        if name not in self._closures:
            self._closures[name] = template_closure(self.environment, name)
        return self._closures[name]

    def provider_templates(self, name: str) -> dict[str, str]:
        """Source of every template a provider contributes, keyed by its address."""
        root = self.template_providers.get(name)
        if root is None:
            return {}
        loader = self._loader(name) or TraversableLoader(root)
        return {
            f"{name}/{template}": loader.get_source(self.environment, template)[0]
            for template in loader.list_templates()
        }

    def _loader(self, name: str) -> TraversableLoader | None:
        prefix_loader = self.environment.loader
        mapping = getattr(prefix_loader, "mapping", {})
        loader = mapping.get(name)
        return loader if isinstance(loader, TraversableLoader) else None

    # Configuration

    def configured(self, kinds: Mapping[str, Mapping[str, Any]]) -> "Registry":
        """A registry whose kinds carry folder and template overrides from config."""
        specs = dict(self.kinds)
        for name, overrides in kinds.items():
            spec = specs[name]
            templates = overrides.get("templates") or {}
            spec = replace(
                spec,
                folder=overrides.get("folder") or spec.folder,
                templates=spec.templates.model_copy(
                    update={k: v for k, v in templates.items() if v is not None}
                ),
            )
            self.check_templates(spec)
            specs[name] = spec
        return replace(self, kinds=specs)

    # Fingerprints

    def fingerprints(self) -> dict[str, str]:
        """Fingerprint of every loaded provider, by name."""
        return {
            provider.name: provider.fingerprint(self.provider_templates(provider.name))
            for provider in self.providers
        }

    def model_fingerprints(self) -> dict[str, str]:
        """Digest of the JSON Schema each kind's models emit (0.1.0:D0005), by kind; for a config
        model override, its code fingerprint as well, since validators never reach a schema.
        """
        result = {}
        for name, spec in sorted(self.kinds.items()):
            schemas: dict[str, Any] = {"records": spec.model.model_json_schema()}
            if spec.core_model is not None:
                schemas["core_document"] = spec.core_model.model_json_schema()
            if spec.model_code is not None:
                schemas["code"] = spec.model_code
            result[name] = digest_of(schemas, allow_float=True)
        return result

    def with_models(
        self,
        kind: str,
        *,
        model: type | None,
        core_model: type | None,
        code: str,
        sites: Mapping[str, str],
    ) -> "Registry":
        """A registry whose `kind` uses consumer subclasses of its provider's models.

        An override must subclass the model it replaces, so the provider's templates and
        defaults keep working (the kind is extended, not redefined).
        """
        spec = self.kinds[kind]
        if model is not None and not (
            isinstance(model, type) and issubclass(model, spec.model)
        ):
            raise ConfigError(
                f"{sites['model']}: {getattr(model, '__name__', model)} is not a subclass of "
                f"{spec.model.__module__}.{spec.model.__name__}, the {kind} model of provider "
                f"{spec.provider}"
            )
        if core_model is not None:
            if spec.core_model is None:
                raise ConfigError(
                    f"{sites['core_model']}: kind {kind} has no core document"
                )
            if not (
                isinstance(core_model, type) and issubclass(core_model, spec.core_model)
            ):
                raise ConfigError(
                    f"{sites['core_model']}: {getattr(core_model, '__name__', core_model)} is not "
                    f"a subclass of {spec.core_model.__module__}.{spec.core_model.__name__}, the "
                    f"{kind} core model of provider {spec.provider}"
                )
        specs = dict(self.kinds)
        specs[kind] = replace(
            spec,
            model=model or spec.model,
            core_model=core_model or spec.core_model,
            model_code=code,
        )
        return replace(self, kinds=specs)

    def all_degradations(self) -> list[Degradation]:
        return [d for provider in self.providers for d in provider.degradations()]

    # Models

    def section_model(self, name: str) -> type[BaseModel]:
        """Model of a kind's section: a `Section` subclass (no privileged path), its core
        document required when the kind has one."""
        spec = self.kinds[name]
        core = spec.core_model or CoreModel
        base = Section[core, spec.model]  # type: ignore[valid-type]
        fields: dict[str, Any] = {}
        if spec.core_model is not None:
            fields["core"] = (
                spec.core_model,
                Field(description="The kind's core document."),
            )
        return create_model(f"{_camel(name)}Section", __base__=base, **fields)

    def root_model(self) -> type[BaseModel]:
        """Generated root model: a `ProjectModel` subclass with one optional section per
        registered kind."""
        fields: dict[str, Any] = {
            name: (self.section_model(name) | None, None) for name in sorted(self.kinds)
        }
        return create_model("ProjectRecords", __base__=ProjectModel, **fields)


RESERVED_CONTEXT = frozenset({"absolute_id", "data_hash", "meta", "refs"})
"""Template context names chancellor sets; a model field may not take them."""


def _check_reserved(model: type, where: str) -> None:
    clash = sorted(RESERVED_CONTEXT & set(getattr(model, "model_fields", {})))
    if clash:
        raise ConfigError(
            f"{where}: field {', '.join(clash)} is reserved in the template context "
            f"({', '.join(sorted(RESERVED_CONTEXT))})"
        )


def _kind_spec(provider: Provider, kind_name: str, decl: Any) -> KindSpec:
    where = f"provider {provider.name}, kind {kind_name}"
    if decl.schema_ is not None:
        raise ConfigError(
            f"{where}: schema-first kinds need the schema extra, which this version does not "
            "ship yet"
        )
    if decl.model is not None:
        model = provider.import_object(decl.model)
        if not (isinstance(model, type) and issubclass(model, Model)):
            raise ConfigError(
                f"{where}: {decl.model} is not a chancellor.api.Model subclass"
            )
    else:
        base = provider.import_object(decl.base) if decl.base else Model
        if not (isinstance(base, type) and issubclass(base, Model)):
            raise ConfigError(
                f"{where}: base {decl.base} is not a chancellor.api.Model subclass"
            )
        model = declarative_model(kind_name, decl.fields, base, where)
    _check_reserved(model, where)
    core_model = None
    if decl.core_model is not None:
        core_model = provider.import_object(decl.core_model)
        if not (isinstance(core_model, type) and issubclass(core_model, CoreModel)):
            raise ConfigError(
                f"{where}: {decl.core_model} is not a chancellor.api.CoreModel subclass"
            )
        _check_reserved(core_model, where)
    return KindSpec(
        name=kind_name,
        provider=provider.name,
        folder=decl.folder,
        templates=decl.templates,
        model=model,
        core_model=core_model,
        aliases=dict(decl.aliases),
    )
