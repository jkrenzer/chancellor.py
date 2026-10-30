"""Loading providers from their three sources.

- built-in: package resources of the distribution (`chancellor.builtin.*`);
- plugins: `chancellor.providers` entry points, sorted by distribution name;
- local: `providers` entries in the configuration, each a folder under the project root.

All three produce a `ManifestProvider` from a manifest; only the fingerprint rule and the way
modules are imported differ. A code provider (built-in, plugin) is fingerprinted by its
distribution's version string, compared exactly. A local provider is declarative and
fingerprinted by a digest over its manifest, its template sources and any module it loads
from its own folder.
"""

import importlib
import logging
from collections.abc import Iterable, Mapping
from datetime import date
from importlib.metadata import entry_points
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    ValidationError,
    create_model,
)

from .api import (
    EXTENSION_POINTS,
    MANIFEST_FILE,
    Degradation,
    FieldDecl,
    Model,
    Provider,
    ProviderManifest,
    RecordRef,
)
from .builtin import BUILTIN_PACKAGES
from .canonical import digest_of
from .codeload import (
    CodeFingerprint,
    code_fingerprint,
    distribution_info,
    load_file_module,
    source_digest,
    tree_digest,
)
from .errors import ConfigError, violations
from .paths import confine, relative
from .yamlio import load as load_yaml
from .yamlio import parse as parse_yaml

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "chancellor.providers"
DISTRIBUTION = "chancellor"

Source = Literal["builtin", "plugin", "local"]


def validate_manifest(data: Any, where: str) -> ProviderManifest:
    """Validate manifest data; unknown keys name the closed set of extension points."""
    if isinstance(data, ProviderManifest):
        return data
    try:
        return ProviderManifest.model_validate(data)
    except ValidationError as exc:
        lines = [f"Invalid provider manifest {where}:", *violations(exc)]
        if any(
            e["type"] == "extra_forbidden" and len(e["loc"]) == 1 for e in exc.errors()
        ):
            lines.append(
                "A manifest contributes only "
                + ", ".join(EXTENSION_POINTS)
                + " besides _api, name and version."
            )
        raise ConfigError("\n".join(lines)) from exc


class ManifestProvider(Provider):
    """A provider read from a manifest, whatever its source."""

    def __init__(
        self,
        manifest: ProviderManifest,
        *,
        base: Traversable,
        source: Source,
        origin: str,
        distribution_name: str | None = None,
        source_root: Traversable | None = None,
    ) -> None:
        self._manifest = manifest
        self.base = base
        self.source = source
        self._origin = origin
        self.distribution_name = distribution_name
        self.source_root = source_root
        """Package tree fingerprinted by content when the distribution is editable."""
        self.code_refs: dict[str, CodeFingerprint] = {}
        """Fingerprints of the modules a local provider's references reached (0.1.0:D0031)."""

    @property
    def manifest(self) -> ProviderManifest:
        return self._manifest

    @property
    def origin(self) -> str:
        return self._origin

    @property
    def code(self) -> bool:
        return self.source != "local"

    def template_root(self) -> Traversable | None:
        if self.manifest.templates is None:
            return None
        return self.base.joinpath(*self.manifest.templates.directory.split("/"))

    def import_object(self, reference: str) -> Any:
        module_name, _, attribute = reference.partition(":")
        if not module_name or not attribute:
            raise ConfigError(
                f"Provider {self.name}: {reference!r} must be written module:attribute"
            )
        module = self._import_module(module_name)
        if self.source == "local" and module_name not in self.code_refs:
            # Every module a local provider references, from its folder or from anywhere on
            # the import path, is fingerprinted by its code (0.1.0:D0031). Code providers are
            # fingerprinted by their distribution instead (0.1.0:D0017).
            from_folder = module.__name__.startswith("_chancellor_local.")
            label = f"{self.name}/{module_name}.py" if from_folder else module_name
            self.code_refs[module_name] = code_fingerprint(module, label=label)
        try:
            return getattr(module, attribute)
        except AttributeError as exc:
            raise ConfigError(
                f"Provider {self.name}: module {module_name} has no {attribute}"
            ) from exc

    def _import_module(self, module_name: str) -> Any:
        if self.source == "local" and isinstance(self.base, Path):
            candidate = self.base.joinpath(*module_name.split(".")).with_suffix(".py")
            if candidate.is_file():
                return self._import_loose(module_name, candidate)
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            raise ConfigError(
                f"Provider {self.name}: cannot import {module_name}: {exc}"
            ) from exc

    def _import_loose(self, module_name: str, path: Path) -> Any:
        try:
            module, source = load_file_module(
                path, f"_chancellor_local.{self.name}.{module_name}"
            )
        except ConfigError as exc:
            raise ConfigError(f"Provider {self.name}: {exc}") from exc
        del source
        return module

    def version_string(self) -> str | None:
        """The version a code provider is fingerprinted by."""
        if self.distribution_name is None:
            return self.manifest.version
        return distribution_info(self.distribution_name)[0]

    def fingerprint(self, template_sources: Mapping[str, str]) -> str:
        if self.code:
            version = self.version_string() or "unversioned"
            editable = (
                distribution_info(self.distribution_name)[1]
                if self.distribution_name
                else False
            )
            if editable and self.source_root is not None:
                # An editable install keeps its version across edits; the source decides.
                return f"{version} source {source_digest(self.source_root)}"
            return version
        return digest_of(
            {
                "manifest": self.manifest.model_dump(mode="json", by_alias=True),
                "templates": dict(sorted(template_sources.items())),
                "modules": {
                    name: fingerprint.value
                    for name, fingerprint in sorted(self.code_refs.items())
                },
            }
        )

    def degradations(self) -> list[Degradation]:
        found: list[Degradation] = []
        if self.code:
            version, editable = (
                distribution_info(self.distribution_name)
                if self.distribution_name
                else (self.manifest.version, False)
            )
            if version is None:
                found.append(
                    Degradation(
                        "unversioned-provider", self.name, "no version string found"
                    )
                )
            if editable:
                found.extend(
                    editable_degradations(self.distribution_name, self.source_root)
                )
        else:
            # Code fingerprinted reliably is no degradation (0.1.0:D0021); only what the code
            # fingerprint could not cover is (0.1.0:D0031).
            for fingerprint in self.code_refs.values():
                found.extend(fingerprint.degradations)
            if self.manifest.version is None:
                if found:
                    found.append(
                        Degradation(
                            "unversioned-provider",
                            self.name,
                            "manifest has no version, and its content cannot be hashed safely",
                        )
                    )
                else:
                    # An info message as long as the content can be hashed safely.
                    logger.info(
                        "provider %s has no version; fingerprinted by its content instead",
                        self.name,
                    )
        return found


def editable_degradations(
    dist: str | None, root: Traversable | None
) -> list[Degradation]:
    """An editable install whose source digest is complete is detected on every
    change, so it is only logged; one whose digest cannot be complete stays a degradation.
    """
    digest = tree_digest(root) if root is not None else None
    if digest is not None and digest.complete:
        logger.info(
            "distribution %s is an editable install; fingerprinted by its complete source",
            dist,
        )
        return []
    reason = digest.reason if digest is not None else "its source tree cannot be found"
    return [
        Degradation(
            "editable-install",
            str(dist),
            f"distribution {dist} is an editable install whose source cannot be fully hashed: "
            f"{reason}",
        )
    ]


def builtin_providers() -> list[ManifestProvider]:
    """The providers shipped in the distribution, in fixed order."""
    result = []
    for package in BUILTIN_PACKAGES:
        base = files(package)
        manifest_file = base.joinpath(MANIFEST_FILE)
        data = parse_yaml(
            manifest_file.read_text("utf-8"), f"{package}/{MANIFEST_FILE}"
        )
        manifest = validate_manifest(data, f"{package}/{MANIFEST_FILE}")
        result.append(
            ManifestProvider(
                manifest,
                base=base,
                source="builtin",
                origin=DISTRIBUTION,
                distribution_name=DISTRIBUTION,
                source_root=files(DISTRIBUTION),
            )
        )
    return result


def plugin_providers() -> list[ManifestProvider]:
    """Providers registered as `chancellor.providers` entry points, by distribution name."""
    found = entry_points(group=ENTRY_POINT_GROUP)
    ordered = sorted(found, key=lambda ep: ((ep.dist.name if ep.dist else ""), ep.name))
    result = []
    for entry_point in ordered:
        where = f"entry point {entry_point.name} ({entry_point.value})"
        try:
            loaded = entry_point.load()
            data = loaded() if callable(loaded) else loaded
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ConfigError(f"Cannot load provider {where}: {exc}") from exc
        manifest = validate_manifest(data, where)
        package = entry_point.module
        try:
            base = files(package)
        except (TypeError, ModuleNotFoundError):
            base = files(package.rpartition(".")[0])
        dist_name = entry_point.dist.name if entry_point.dist else None
        result.append(
            ManifestProvider(
                manifest,
                base=base,
                source="plugin",
                origin=dist_name or package,
                distribution_name=dist_name,
                source_root=files(package.partition(".")[0]),
            )
        )
    return result


def local_providers(
    entries: Iterable[Mapping[str, str]], root: Path
) -> list[ManifestProvider]:
    """Providers declared in the configuration, in declared order."""
    result = []
    for entry in entries:
        name, path = entry["name"], entry["path"]
        folder = confine(root, path, setting=f"providers[{name}].path")
        manifest_file = folder / MANIFEST_FILE
        if not manifest_file.is_file():
            raise ConfigError(
                f"Provider {name} is declared in config, but {relative(root, folder)}/"
                f"{MANIFEST_FILE} does not exist"
            )
        where = relative(root, manifest_file)
        manifest = validate_manifest(load_yaml(manifest_file, error=ConfigError), where)
        if manifest.name != name:
            raise ConfigError(
                f"Provider declared as {name} in config, but {where} names itself "
                f"{manifest.name}"
            )
        result.append(
            ManifestProvider(
                manifest, base=folder, source="local", origin=relative(root, folder)
            )
        )
    return result


# Declarative kinds


def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("must contain non-whitespace text")
    return value


def _none_to_empty(value: Any) -> Any:
    return [] if value is None else value


_SCALARS: dict[str, Any] = {
    "str": str,
    "text": Annotated[str, Field(min_length=1), AfterValidator(_nonblank)],
    "int": int,
    "bool": bool,
    "date": date,
    "record_ref": Annotated[str, RecordRef()],
}


def _field_type(text: str, where: str, depends: str = "id") -> tuple[Any, bool]:
    """Python type of a declared field type and whether it is a list."""
    # chains (deferred, 0.1.0:D0033): a declarative way to ask for chained data references would be
    # read here, next to `depends`, e.g. a depth or a `follow` setting on the field.
    ref = Annotated[str, RecordRef(depends=depends)]  # type: ignore[arg-type]
    scalars = {**_SCALARS, "record_ref": ref}
    spelled = text.replace(" ", "")
    if spelled.startswith("list[") and spelled.endswith("]"):
        inner = spelled[5:-1]
        if inner in scalars:
            return (
                Annotated[list[scalars[inner]], BeforeValidator(_none_to_empty)],
                True,
            )
    elif spelled in scalars:
        return scalars[spelled], False
    allowed = ", ".join([*_SCALARS, "list[...]"])
    raise ConfigError(f"{where}: unknown field type {text!r}; use one of {allowed}")


def declarative_model(
    name: str, fields: Mapping[str, FieldDecl], base: type[Model], where: str
) -> type[Model]:
    """Build a record model from declared fields on top of `base`."""
    definitions: dict[str, Any] = {}
    for field_name, decl in fields.items():
        annotation, is_list = _field_type(
            decl.type, f"{where}.fields.{field_name}", decl.depends
        )
        if decl.required:
            default = Field(description=decl.description)
        elif is_list:
            default = Field(default_factory=list, description=decl.description)
        else:
            annotation = annotation | None
            default = Field(default=None, description=decl.description)
        definitions[field_name] = (annotation, default)
    camel = "".join(part.capitalize() for part in name.replace("-", "_").split("_"))
    return create_model(f"{camel}Record", __base__=base, **definitions)
