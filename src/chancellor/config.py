"""Chancellor's configuration: `_api/chancellor` and `config/chancellor` (0.1.0:D0004).

Loading is two-phase. Phase one reads `_api/<key>`, `config/<key>/providers` and
`config/<key>/include` from the main data file against a fixed bootstrap schema, so the
provider list never depends on a provider. Phase two builds the merged model from the
registry — chancellor's own keys plus one section per registered kind with its provider's
defaults — and validates all of `config/<key>` against it.

The values arrive through a pydantic-settings source stack, ordered once: environment
(`CHANCELLOR_*`, nested with `__`), the config loader reading the data tree, provider
defaults, built-in defaults. YAML is read with ruamel.yaml by `DataTreeSource`, not by the
PyYAML-based source of pydantic-settings.
"""

import difflib
import logging
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from .api import (
    ApiMeta,
    ChancellorConfig,
    ConfigLoader,
    KindConfig,
    KindTemplatesConfig,
    LoadedConfig,
    ProviderEntry,
)
from .canonical import digest_of
from .errors import ConfigError, location_text
from .keys import ModuleKeys
from .registry import Registry
from .yamlio import parse_plain_value

logger = logging.getLogger(__name__)

DATA_API_VERSION = "2.0.0"
"""Format version of the data tree, independent of the package version."""

DATA_KIND = "project_records"

ENV_PREFIX = "CHANCELLOR_"

DEFAULT_LOADERS = ("builtin.data_file",)
"""Config loaders when `config/<key>/loaders` is not set (0.1.0:D0034)."""

BOOTSTRAP_KEYS = frozenset({"providers", "include", "loaders", "data_model"})
"""Keys read before any configuration source exists; `--set` cannot reach them."""

LAYOUT_KEYS = frozenset({"include", "loaders"})
"""Config keys about file layout; they never enter the config digest."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Bootstrap(_Strict):
    """What phase one reads before any provider is loaded."""

    api: ApiMeta
    providers: list[ProviderEntry] = Field(default_factory=list)
    include: list[str] = Field(default_factory=list)
    data_model: str | None = None
    loaders: list[str | dict[str, Any]] = Field(
        default_factory=lambda: list(DEFAULT_LOADERS)
    )


def bootstrap(main: Mapping[str, Any], keys: ModuleKeys, where: str) -> Bootstrap:
    """Phase one: `_api`, the provider list and the includes, from the main file only."""
    api = (main.get("_api") or {}).get(keys.api)
    if api is None:
        raise ConfigError(
            f'{where}: missing _api.{keys.api}; expected version: "{DATA_API_VERSION}" and '
            f"kind: {DATA_KIND}"
        )
    config = (main.get("config") or {}).get(keys.config) or {}
    providers = ((main.get("config") or {}).get(keys.providers) or {}).get(
        "providers", []
    )
    try:
        return Bootstrap(
            api=api,
            providers=providers,
            include=config.get("include", []),
            data_model=config.get("data_model"),
            loaders=config.get("loaders", list(DEFAULT_LOADERS)),
        )
    except ValidationError as exc:
        lines = [f"{where}: invalid bootstrap configuration:"]
        for error in exc.errors():
            location = location_text(error["loc"])
            location = (
                location.replace("api", f"_api.{keys.api}", 1)
                if location.startswith("api")
                else f"config.{keys.config}.{location}"
            )
            lines.append(f"- {location}: {error['msg']}")
        raise ConfigError("\n".join(lines)) from exc


class DataTreeLoader(ConfigLoader):
    """`builtin.data_file`: `config/<key>` from the merged data tree, the default loader."""

    def load(self) -> LoadedConfig:
        config = self.context.tree.get("config") or {}
        data = config.get(self.context.keys.config) or {}
        files = self.context.files
        return LoadedConfig(
            data=data if isinstance(data, Mapping) else {},
            origin=files[0] if files else "",
            sources=files,
        )


class DataTreeSource(PydanticBaseSettingsSource):
    """Pydantic-settings source over what a `ConfigLoader` returned."""

    def __init__(self, settings_cls: type[BaseSettings], loaded: LoadedConfig) -> None:
        super().__init__(settings_cls)
        self.loaded = loaded

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        return self.loaded.data.get(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        return dict(self.loaded.data)


def consumer_kind_defaults(base: type[ChancellorConfig]) -> dict[str, dict[str, Any]]:
    """The `kinds` defaults a consumer's `ChancellorConfig` subclass sets, per kind, holding
    only the fields set explicitly (recursively), so an explicit value wins even when it equals
    the built-in default."""
    info = base.model_fields["kinds"]
    default = info.get_default(call_default_factory=True) or {}
    result: dict[str, dict[str, Any]] = {}
    for kind, value in dict(default).items():
        if isinstance(value, BaseModel):
            result[kind] = value.model_dump(exclude_unset=True)
        elif isinstance(value, Mapping):
            result[kind] = dict(value)
    return result


def _kind_config_class(base: type[ChancellorConfig]) -> type[KindConfig]:
    """The consumer's `KindConfig` subclass, if `kinds` is typed `dict[str, MyKindConfig]`."""
    for argument in get_args(base.model_fields["kinds"].annotation):
        if isinstance(argument, type) and issubclass(argument, KindConfig):
            return argument
    return KindConfig


def _kind_model(
    registry: Registry,
    name: str,
    kind_class: type[KindConfig] = KindConfig,
    consumer: Mapping[str, Any] | None = None,
) -> type[BaseModel]:
    """`KindConfig` for one kind. Each field's default comes from the consumer's class default
    (its explicitly set fields), else the provider's default, else the built-in default; a
    source that sets part of the kind keeps the other fields' defaults."""
    spec = registry.kinds[name]
    consumer = dict(consumer or {})
    templates_set = dict(consumer.pop("templates", None) or {})
    templates = create_model(
        f"{name}_templates",
        __base__=KindTemplatesConfig,
        records=(
            str,
            Field(default=templates_set.get("records", spec.templates.records)),
        ),
        core_document=(
            str | None,
            Field(
                default=templates_set.get("core_document", spec.templates.core_document)
            ),
        ),
    )
    fields: dict[str, Any] = {
        "folder": (
            str | None,
            Field(
                default=consumer.pop("folder", spec.folder),
                description="Output folder of the kind.",
            ),
        ),
        "templates": (templates, Field(default_factory=templates)),
    }
    for key, value in consumer.items():
        info = kind_class.model_fields[key]
        fields[key] = (
            info.annotation,
            Field(default=value, description=info.description),
        )
    return create_model(f"{name}_config", __base__=kind_class, **fields)


def config_model(
    registry: Registry,
    loaded: Sequence[LoadedConfig] | LoadedConfig | None = None,
    base: type[ChancellorConfig] = ChancellorConfig,
) -> type[BaseSettings]:
    """The merged config model (0.1.0:D0004): built on top of `base`, so a consumer's subclass of
    `ChancellorConfig` (its defaults, fields and validators) is the one config authority.
    `kinds` has one typed section per registered kind whose defaults merge per field:
    consumer class default, then provider default, then built-in default. Every other nested
    value is replaced whole by a higher source."""
    consumer = consumer_kind_defaults(base)
    unknown = sorted(set(consumer) - set(registry.kinds))
    if unknown:
        raise ConfigError(
            f"{base.__name__}: kinds default for {', '.join(unknown)}, which no provider "
            f"registers; registered kinds: {', '.join(sorted(registry.kinds))}"
        )
    kind_class = _kind_config_class(base)
    kind_fields: dict[str, Any] = {}
    for name in sorted(registry.kinds):
        model = _kind_model(registry, name, kind_class, consumer.get(name))
        kind_fields[name] = (model, Field(default_factory=model))
    kinds = create_model(
        "KindsConfig", __config__=ConfigDict(extra="forbid"), **kind_fields
    )
    if loaded is None:
        source_data: tuple[LoadedConfig, ...] = ()
    elif isinstance(loaded, LoadedConfig):
        source_data = (loaded,)
    else:
        source_data = tuple(loaded)

    class _Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_prefix=ENV_PREFIX, env_nested_delimiter="__", extra="forbid"
        )
        loaded_configs: ClassVar[tuple[LoadedConfig, ...]] = source_data

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            del dotenv_settings, file_secret_settings
            # Highest first: CLI (`--set`, as init arguments), environment, the loaders in
            # declared order; class defaults below them.
            return (
                init_settings,
                env_settings,
                *(DataTreeSource(settings_cls, item) for item in cls.loaded_configs),
            )

    return create_model(
        "ChancellorSettings",
        __base__=(_Settings, base),
        kinds=(kinds, Field(default_factory=kinds)),
    )


def load_config(
    registry: Registry,
    loaded: Sequence[LoadedConfig],
    keys: ModuleKeys,
    base: type[ChancellorConfig] = ChancellorConfig,
    overrides: Mapping[str, Any] | None = None,
) -> tuple[Any, str]:
    """Phase two: the validated configuration and its digest. `overrides` (from `--set`) is
    the highest-priority source."""
    logger.debug(
        "config sources, highest first: CLI %s, environment (%s*), loaders %s, class "
        "defaults, provider defaults, built-in defaults",
        sorted(flatten(overrides or {})),
        ENV_PREFIX,
        [list(item.sources) or item.origin for item in loaded],
    )
    model = config_model(registry, loaded, base)
    try:
        settings = model(**dict(overrides or {}))
    except ValidationError as exc:
        raise ConfigError(_config_errors(exc, model, keys, registry)) from exc
    return settings, config_digest(settings)


def parse_overrides(pairs: Sequence[str]) -> dict[str, Any]:
    """`--set KEY=VALUE` pairs as a nested mapping below `config/<key>` (0.1.0:D0034).

    `KEY` is dotted; `VALUE` is YAML read with the safe loader, and tags and anchors are
    refused, so a value can only be plain data. Bootstrap keys cannot be set this way.
    """
    result: dict[str, Any] = {}
    for pair in pairs:
        key, sep, text = pair.partition("=")
        key = key.strip()
        if not sep or not key or any(not part for part in key.split(".")):
            raise ConfigError(
                f"--set {pair!r}: write it as KEY=VALUE, e.g. wrap_width=80"
            )
        if key.split(".")[0] in BOOTSTRAP_KEYS:
            raise ConfigError(
                f"--set {key}: {', '.join(sorted(BOOTSTRAP_KEYS))} are read before any source; "
                "set them in the data file"
            )
        value = parse_plain_value(text, f"--set {key}")
        node = result
        parts = key.split(".")
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise ConfigError(f"--set {key}: {part} is already set to a value")
            node = child
        node[parts[-1]] = value
    return result


def flatten(mapping: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    """`{"a": {"b": 1}}` as `{"a.b": 1}`."""
    flat: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, Mapping):
            flat.update(flatten(value, f"{prefix}{key}."))
        else:
            flat[f"{prefix}{key}"] = value
    return flat


def config_digest(settings: BaseModel) -> str:
    """Digest of the whole validated configuration, file-layout keys excluded: `include` and
    each kind's `data` path only say where data is read from (0.1.0:D0019)."""
    data = settings.model_dump(mode="json", exclude=set(LAYOUT_KEYS))
    for kind in (data.get("kinds") or {}).values():
        if isinstance(kind, dict):
            kind.pop("data", None)
    return digest_of(data)


def _config_errors(
    exc: ValidationError, model: type[BaseModel], keys: ModuleKeys, registry: Registry
) -> str:
    lines = [f"Invalid configuration in config.{keys.config}:"]
    for error in exc.errors():
        location = location_text(error["loc"], f"config.{keys.config}")
        line = f"- {location}: {error['msg']}"
        if error["type"] == "extra_forbidden":
            valid = _keys_at(model, error["loc"][:-1])
            near = difflib.get_close_matches(str(error["loc"][-1]), valid, n=3)
            if near:
                line += f"; did you mean {', '.join(near)}?"
            line += f" (providers loaded: {', '.join(registry.provider_names())})"
        lines.append(line)
    return "\n".join(lines)


def _keys_at(model: type[BaseModel], loc: tuple[int | str, ...]) -> list[str]:
    current: Any = model
    for part in loc:
        if isinstance(part, int):
            continue
        fields = getattr(current, "model_fields", {})
        if part not in fields:
            return []
        current = fields[part].annotation
    return list(getattr(current, "model_fields", {}))
