"""Public extension interfaces of chancellor (0.1.0:D0009).

Everything a consumer may subclass or implement lives here, and chancellor's own built-in
types implement these same classes, on no privileged path. A change to a signature in this
module is a breaking change of the distribution.

Extension points, one base class each:

- `Model` and `CoreModel`: a record kind's data model, with six hooks (0.1.0:D0009);
- `Provider`: a bundle contributing kinds, templates, formatters, linters, config loaders;
- `Formatter`: shapes rendered text, e.g. wraps Markdown;
- `Linter`: checks written documents;
- `ConfigLoader`: delivers chancellor's configuration and its digest.

A consumer may also supply its own root model; its contract is the `RootModel` protocol.
"""

import string
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib.resources.abc import Traversable
from pathlib import Path
from types import NoneType, UnionType
from typing import (
    Annotated,
    Any,
    ClassVar,
    Generic,
    Literal,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    Union,
    get_args,
    get_origin,
    runtime_checkable,
)

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    GetJsonSchemaHandler,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

from .keys import ModuleKeys

# Markers


@dataclass(frozen=True)
class _SchemaMarker:
    """Annotated marker that also writes a flag into the emitted JSON Schema.

    Because the flag travels into the schema, the set of marked fields is covered by the
    model's fingerprint (0.1.0:D0005, 0.1.0:D0006).
    """

    schema_key: ClassVar[str]

    def __get_pydantic_json_schema__(
        self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(core_schema)
        schema[self.schema_key] = True
        return schema


@dataclass(frozen=True)
class DigestExclude(_SchemaMarker):
    """Keeps a field out of `model_canonicalize`, and therefore out of `data_hash` (0.1.0:D0006)."""

    schema_key: ClassVar[str] = "x-chancellor-digest-exclude"


@dataclass(frozen=True)
class Generated(DigestExclude):
    """A field chancellor fills in, such as a core document's index; rejected as input."""

    schema_key: ClassVar[str] = "x-chancellor-generated"


@dataclass(frozen=True)
class Version(_SchemaMarker):
    """Marks a string field as a version (0.1.0:D0036). Under a configured scheme other than `free`,
    every marked value must parse, and in a list of models carrying a marked field the versions
    increase in list order, oldest first."""

    schema_key: ClassVar[str] = "x-chancellor-version"


Depends: TypeAlias = Literal["id", "name", "data"]
"""What a document depends on when it holds a reference (0.1.0:D0032): the target's ID only,
also its document's file name, or also its data."""


@dataclass(frozen=True)
class RecordRef(_SchemaMarker):
    """Marks a string as a reference to another record by ID, with what flows over it.

    Use it as annotation metadata: `Annotated[str, RecordRef()]`, or
    `Annotated[str, RecordRef(depends="data")]`. `depends` says what the referencing document
    may read of the target, and so when it rebuilds (0.1.0:D0032):

    - `"id"` (default): the ID only. A change in the target never rebuilds the document.
    - `"name"`: also the target document's file name and path, e.g. for a link; a rename
      rebuilds.
    - `"data"`: also the target's serialized data; any change in its data rebuilds.

    Templates see exactly that under `refs.<field>`, and nothing more, so a template cannot read
    what the digest does not cover. A value shaped like an ID of a registered kind must resolve
    to a record; any other value is an external identifier and is kept as written. The flow is
    written into the JSON Schema, so it is part of the model fingerprint.
    """

    depends: Depends = "id"
    schema_key: ClassVar[str] = "x-chancellor-record-ref"

    def __post_init__(self) -> None:
        if self.depends not in ("id", "name", "data"):
            raise ValueError(f"depends must be id, name or data, not {self.depends!r}")

    def __get_pydantic_json_schema__(
        self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(core_schema)
        schema[self.schema_key] = self.depends
        return schema


def _blank_to_none(value: Any) -> Any:
    return None if isinstance(value, str) and not value.strip() else value


def _none_to_empty(value: Any) -> Any:
    return [] if value is None else value


RecordRefs: TypeAlias = Annotated[
    list[Annotated[str, RecordRef()]], BeforeValidator(_none_to_empty)
]
"""List of record references by ID (`depends="id"`); omitted or null means none."""


def _field_has(info: FieldInfo, marker: type) -> bool:
    return any(isinstance(item, marker) for item in info.metadata)


def marked_fields(model: type[BaseModel], marker: type) -> frozenset[str]:
    """Names of the fields of `model` annotated with `marker` (or a subclass of it)."""
    return frozenset(
        name for name, info in model.model_fields.items() if _field_has(info, marker)
    )


@dataclass(frozen=True)
class RefLink:
    """One reference a record holds: the field it sits in, what flows over it, the target ID."""

    field: str
    depends: Depends
    id: str


def _annotation_links(value: Any, annotation: Any, path: str) -> list[RefLink]:
    if value is None:
        return []
    origin = get_origin(annotation)
    if origin is Annotated:
        base, *metadata = get_args(annotation)
        markers = [item for item in metadata if isinstance(item, RecordRef)]
        if markers:
            return (
                [RefLink(path, markers[0].depends, value)]
                if isinstance(value, str)
                else []
            )
        return _annotation_links(value, base, path)
    if origin in (Union, UnionType):
        found: list[RefLink] = []
        for option in get_args(annotation):
            found = _annotation_links(value, option, path)
            if found:
                break
        return found
    if origin in (list, tuple, set, frozenset) and isinstance(value, list | tuple):
        args = get_args(annotation)
        item_type = args[0] if args else Any
        return [
            link for item in value for link in _annotation_links(item, item_type, path)
        ]
    if isinstance(value, BaseModel):
        return collect_ref_links(value, prefix=f"{path}.")
    return []


def collect_ref_links(instance: BaseModel, prefix: str = "") -> list[RefLink]:
    """Every reference in `instance`, nested models included, in field order."""
    links: list[RefLink] = []
    for name, info in type(instance).model_fields.items():
        value = getattr(instance, name)
        markers = [item for item in info.metadata if isinstance(item, RecordRef)]
        if markers:
            if isinstance(value, str):
                links.append(RefLink(prefix + name, markers[0].depends, value))
        else:
            links.extend(_annotation_links(value, info.annotation, prefix + name))
    return links


def collect_refs(instance: BaseModel) -> list[str]:
    """Every `RecordRef` value in `instance`, nested models included, in field order."""
    return [link.id for link in collect_ref_links(instance)]


# Models


@dataclass(frozen=True)
class Origin:
    """Where a piece of raw data came from: a file and a location inside it."""

    file: str
    location: str = ""


@dataclass(frozen=True)
class RecordIndex:
    """What the indexing pass learns about a record: its key and the keys it points to."""

    id: str
    refs: tuple[str, ...] = ()


class Model(BaseModel):
    """Base class of every record model. Subclass it to define a record kind.

    Validation is Pydantic's; unknown inputs are rejected. Six hooks shape what chancellor
    does with a record, named as Pydantic names things (0.1.0:D0009):

    1. `model_load` (classmethod): turns raw source data into validation input. Override it
       to read another input shape, e.g. to import records from Markdown.
    2. `model_validate`: Pydantic's validation, unchanged.
    3. `model_canonicalize`: the data behind `data_hash`; `DigestExclude` fields and computed
       fields are left out.
    4. `model_index`: the record's ID and the IDs it references, so refs are findable.
    5. `model_serialize`: the document data templates and front matter see.
    6. `model_save`: the data written back into the data tree.

    `front_matter` names the keys of `model_serialize` written into a document's front
    matter, in order; `None` writes none. `inverse_refs` maps a `RecordRef` field to the field
    of the referenced record that must list this record back, e.g. `{"addresses":
    "addressed_by"}`; `doctor` reports one-sided links. `output_name` gives the file name of
    the record's document.

    Minimal subclass:

    ```python
    from chancellor.api import Model, RecordRefs

    class Task(Model):
        title: str
        depends_on: RecordRefs = []
        front_matter = ("id", "title")
    ```
    """

    model_config = ConfigDict(extra="forbid")

    front_matter: ClassVar[tuple[str, ...] | None] = None
    inverse_refs: ClassVar[Mapping[str, str]] = {}

    id: str = Field(description="Record identifier, unique within the project.")

    @model_validator(mode="before")
    @classmethod
    def _reject_generated_inputs(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            given = sorted(marked_fields(cls, Generated) & data.keys())
            if given:
                raise ValueError(
                    f"{', '.join(given)} generated by chancellor; remove from the input"
                )
        return data

    @classmethod
    def model_load(cls, raw: Any, *, origin: Origin | None = None) -> Any:
        """Hook 1: raw source data to validation input; the default passes it through."""
        del origin
        return raw

    def model_canonicalize(self) -> Any:
        """Hook 3: JSON data behind `data_hash`, with every default filled in."""
        excluded = marked_fields(type(self), DigestExclude) | set(
            type(self).model_computed_fields
        )
        return self.model_dump(mode="json", by_alias=True, exclude=set(excluded))

    def model_index(self) -> RecordIndex:
        """Hook 4: the record's ID and every `RecordRef` it holds."""
        return RecordIndex(id=self.id, refs=tuple(collect_refs(self)))

    def model_serialize(self) -> dict[str, Any]:
        """Hook 5: document data for templates and front matter, computed fields included."""
        return self.model_dump(mode="json", by_alias=True)

    def model_save(self) -> Any:
        """Hook 6: data written back into the data tree; generated and computed fields go."""
        excluded = marked_fields(type(self), Generated) | set(
            type(self).model_computed_fields
        )
        return self.model_dump(
            mode="json", by_alias=True, exclude=set(excluded), exclude_defaults=True
        )

    def output_name(self, suffix: str) -> str:
        """File name of this record's document; `suffix` comes from the template, e.g. `.md`."""
        return f"{self.id}{suffix}"


class CoreModel(Model):
    """Base class of a kind's core document: one per kind, indexing the kind's records."""

    @abstractmethod
    def index_records(self, records: Sequence[Model], *, suffix: str = ".md") -> Self:
        """Return a copy of this core document with its generated index filled in.

        `suffix` is the output suffix of the kind's records template, e.g. `.md`, so that links
        in the index match the files the records are written to.
        """


# Data tree models: inheritable bases for root, config and sections (0.1.0:D0030)


class _Tree(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ApiMeta(_Tree):
    """`_api/chancellor`: identifies the data tree as chancellor input and its format."""

    version: Literal["2.0.0"] = Field(description='Format version; quote it ("2.0.0").')
    kind: Literal["project_records"] = Field(description="Always `project_records`.")


class ProviderEntry(_Tree):
    """A local provider: its name and its folder under the project root."""

    name: str = Field(description="Provider name, as its manifest declares it.")
    path: str = Field(description="Provider folder, relative to the project root.")


class TypeRef(BaseModel):
    """A formatter or linter: its type address plus the type's own arguments."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(
        description="Type address, e.g. `builtin.mdformat`, or `module:Class`."
    )

    def arguments(self) -> dict[str, Any]:
        """The type's own arguments: every key besides `type`."""
        return dict(self.model_extra or {})


class KindTemplatesConfig(_Tree):
    """Template overrides of one kind; unset means the provider's template."""

    records: str | None = Field(
        default=None, description="Template of the kind's records."
    )
    core_document: str | None = Field(
        default=None, description="Template of the kind's core document."
    )


class KindConfig(_Tree):
    """`config/chancellor/kinds/<kind>`; every unset key keeps the provider's default."""

    folder: str | None = Field(default=None, description="Output folder of the kind.")
    data: str | None = Field(
        default=None,
        description=(
            "File holding the kind's data (its section: `core` and `records`), relative to "
            "the project root; chancellor reads the kind's records from it (0.1.0:D0019)."
        ),
    )
    # shared data file (future, 0.1.0:D0019): a `key` setting next to `data` will name the path to
    # the kind's section inside a file shared by several kinds; `datatree.location_for` turns
    # both into a `DataLocation`.
    templates: KindTemplatesConfig = Field(default_factory=KindTemplatesConfig)
    model: str | None = Field(
        default=None,
        description=(
            "Subclass of the provider's record model, as path/to/file.py:Class "
            "(relative to the project root) or module:Class."
        ),
    )
    core_model: str | None = Field(
        default=None, description="Subclass of the provider's core model, likewise."
    )


class VersioningConfig(_Tree):
    """How the project writes versions (0.1.0:D0036): the scheme validated, and the format of
    absolute record IDs."""

    scheme: str = Field(
        default="free",
        description=(
            "Version scheme: `semver` (Semantic Versioning 2.0.0), `pep440`, `free` (no checks "
            "beyond the record models' own), a provider's type address, or an import path "
            "`path/to/file.py:Class` / `module:Class`."
        ),
    )
    absolute_id: str = Field(
        default="{version}:{id}",
        description="Format of an absolute record ID, with the fields `{version}` and `{id}`.",
    )

    @field_validator("absolute_id")
    @classmethod
    def _format_fields(cls, value: str) -> str:
        fields = {
            name
            for _, name, _, _ in string.Formatter().parse(value)
            if name is not None
        }
        if "id" not in fields:
            raise ValueError("must contain the field {id}")
        unknown = sorted(fields - {"id", "version"})
        if unknown:
            raise ValueError(
                f"unknown field {', '.join(unknown)}; use {{version}} and {{id}}"
            )
        return value


class ChancellorConfig(_Tree):
    """`config/chancellor`: chancellor's own settings, with their defaults.

    Subclass it to change a default or add a field and validator of your own; name the
    subclass in your root model's `ConfigTree`. Chancellor builds its merged configuration on
    top of the subclass, so additions survive, appear in `schema config` and enter the digest.
    """

    providers: list[ProviderEntry] = Field(default_factory=list)
    include: list[str] = Field(
        default_factory=list, description="Further data files or folders to merge."
    )
    wrap_width: int = Field(
        default=100, gt=0, description="Width rendered prose wraps at."
    )
    formatter: TypeRef = Field(default_factory=lambda: TypeRef(type="builtin.mdformat"))
    linter: TypeRef = Field(default_factory=lambda: TypeRef(type="builtin.none"))
    kinds: dict[str, KindConfig] = Field(
        default_factory=dict,
        description="Per-kind folders, templates and model overrides.",
    )
    data_model: str | None = Field(
        default=None, description="Root model as path/to/file.py:Class or module:Class."
    )
    loaders: list[str | dict[str, Any]] = Field(
        default_factory=lambda: ["builtin.data_file"],
        description=(
            "Config loaders, highest priority first: a type address or import path, or a "
            "mapping with `type` and the loader's arguments."
        ),
    )
    snapshot: str | None = Field(
        default=None, description="Write the validated data as JSON to this path."
    )
    lock: str = Field(default="chancellor.lock", description="Lock file path.")
    versioning: VersioningConfig = Field(
        default_factory=VersioningConfig,
        description="Version scheme and absolute-ID format.",
    )


class MetaInfo(_Tree):
    """`meta/chancellor`: facts about the record set as a whole (0.1.0:D0036)."""

    version: str | None = Field(
        default=None,
        description="Version of the record set; quote it in YAML. Absolute IDs combine it with "
        "a record ID.",
    )


class MetaTree(BaseModel):
    """`meta`: one entry per module. Override the field's alias to move chancellor's key."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    chancellor: MetaInfo | None = Field(
        default=None, description="chancellor's `meta` entry."
    )


class ApiTree(BaseModel):
    """`_api`: one entry per module. Override the field's alias to move chancellor's key."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    chancellor: ApiMeta | None = Field(
        default=None, description="chancellor's `_api` entry."
    )


class ConfigTree(BaseModel):
    """`config`: one entry per module; other modules' entries are kept, never validated."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    chancellor: ChancellorConfig = Field(
        default_factory=ChancellorConfig, description="chancellor's configuration."
    )


CoreT = TypeVar("CoreT", bound=CoreModel)
RecordT = TypeVar("RecordT", bound=Model)


class Section(BaseModel, Generic[CoreT, RecordT]):
    """One kind's data: its core document, if the kind has one, and its records.

    Record IDs are unique, the core is not among the records, and records are ordered by ID.
    `Section[DecisionCore, Decision]` is the decisions' section of the built-in flavour.
    """

    model_config = ConfigDict(extra="forbid")

    core: CoreT | None = Field(default=None, description="The kind's core document.")
    records: list[RecordT] = Field(
        default_factory=list, description="The kind's records."
    )

    @model_validator(mode="after")
    def _unique_and_ordered(self) -> Self:
        ids = [record.id for record in self.records]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate record IDs: {', '.join(duplicates)}")
        if self.core is not None and self.core.id in ids:
            raise ValueError(
                f"records must not contain the core document {self.core.id}"
            )
        self.records = sorted(self.records, key=lambda record: record.id)
        return self


def section_types(section: type[BaseModel]) -> tuple[Any, Any]:
    """The core and record types a `Section` subclass declares."""
    core = section.model_fields["core"].annotation
    core_args = [a for a in get_args(core) if a is not NoneType] or [core]
    records = get_args(section.model_fields["records"].annotation)
    return core_args[0], (records[0] if records else Model)


def _section_class(annotation: Any) -> type[BaseModel] | None:
    if isinstance(annotation, type) and issubclass(annotation, Section):
        return annotation
    for argument in get_args(annotation):
        found = _section_class(argument)
        if found is not None:
            return found
    return None


class ProjectModel(BaseModel):
    """Base of every root model: `_api`, `config`, and one `Section` field per kind.

    The generated root model is a subclass, and so is a supplied one (`data_model`): declare a
    field per kind, typed with that kind's `Section`, and inherit every other field and its
    default. To change configuration defaults, subclass `ConfigTree` and `ChancellorConfig`
    and use `Field(default_factory=...)`. Sections of other tools are ignored.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    api: ApiTree = Field(default_factory=ApiTree, alias="_api")
    meta: MetaTree = Field(default_factory=MetaTree)
    config: ConfigTree = Field(default_factory=ConfigTree)

    @classmethod
    def section_fields(cls) -> dict[str, type[BaseModel]]:
        """Kind name (field alias or name) to the `Section` subclass declared for it."""
        result = {}
        for name, info in cls.model_fields.items():
            section = _section_class(info.annotation)
            if section is not None:
                result[info.alias or name] = section
        return result

    def chancellor_sections(
        self,
    ) -> Mapping[str, tuple[CoreModel | None, Sequence[Model]]]:
        """Per kind: its core document (or `None`) and its records, for every set section."""
        result = {}
        for name, info in type(self).model_fields.items():
            value = getattr(self, name)
            if isinstance(value, Section):
                result[info.alias or name] = (value.core, list(value.records))
        return result


# Root model


@runtime_checkable
class RootModel(Protocol):
    """Contract of a consumer-supplied root model (0.1.0:D0030), named as `data_model` in config.

    The class is a Pydantic model; chancellor validates the record sections of the data tree
    with it (everything except `_api` and `config`). It exposes per kind the core document
    (or `None`) and the records; chancellor supplies canonicalization, hashing, ref
    extraction and rendering in return.
    """

    def chancellor_sections(
        self,
    ) -> Mapping[str, tuple[CoreModel | None, Sequence[Model]]]:
        """Per kind name: its core document (or `None`) and its records."""
        ...  # pylint: disable=unnecessary-ellipsis


# Providers


EXTENSION_POINTS = (
    "kinds",
    "templates",
    "formatters",
    "linters",
    "config_loaders",
    "version_schemes",
)
"""The closed set of things a provider may contribute."""

MANIFEST_FILE = "chancellor-provider.yaml"


def _version_text(value: Any) -> Any:
    return (
        str(value) if isinstance(value, int) and not isinstance(value, bool) else value
    )


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ManifestApi(_Strict):
    """Identifies a provider manifest and the manifest format version."""

    version: Literal["1.0.0"] = Field(description="Manifest format version.")
    kind: Literal["chancellor_provider"] = Field(
        description="Always `chancellor_provider`."
    )


class FieldDecl(_Strict):
    """A field of a declaratively defined kind."""

    type: str = Field(
        examples=[
            "str",
            "text",
            "int",
            "bool",
            "date",
            "record_ref",
            "list[record_ref]",
        ],
        description=(
            "Field type: `str`, `text` (nonblank string), `int`, `bool`, `date`, "
            "`record_ref`, or `list[...]` of one of these."
        ),
    )
    required: bool = Field(default=True, description="Whether the field must be given.")
    depends: Depends = Field(
        default="id",
        description=(
            "For `record_ref` fields: what the document reads of the target and so rebuilds "
            "on: `id`, `name` (file name and path) or `data`."
        ),
    )
    description: str | None = Field(default=None, description="Help text for authors.")


class KindTemplates(_Strict):
    """Templates of a kind, addressed as `<provider>/<name>`."""

    records: str = Field(description="Template of the kind's records.")
    core_document: str | None = Field(
        default=None, description="Template of the kind's core document, if it has one."
    )


class KindDecl(_Strict):
    """A record kind contributed by a provider. The manifest holds binding keys only."""

    folder: str = Field(
        description="Default output folder, relative to the project root."
    )
    templates: KindTemplates
    model: str | None = Field(
        default=None,
        description="Record model as `module:Class`, a `chancellor.api.Model`.",
    )
    core_model: str | None = Field(
        default=None,
        description="Core document model as `module:Class`, a `CoreModel`.",
    )
    schema_: str | None = Field(
        default=None,
        alias="schema",
        description="JSON Schema to build the model from at load; needs the `schema` extra.",
    )
    fields: dict[str, FieldDecl] | None = Field(
        default=None, description="Declarative fields; the model is built at load."
    )
    base: str | None = Field(
        default=None,
        description="Base model of declarative fields as `module:Class`; default `Model`.",
    )
    aliases: dict[str, Literal["records", "core_document"]] = Field(
        default_factory=dict,
        description="Extra names for the kind's documents, e.g. `adr: records`.",
    )

    @model_validator(mode="after")
    def _one_model_source(self) -> "KindDecl":
        sources = [s for s in (self.model, self.fields, self.schema_) if s is not None]
        if len(sources) != 1:
            raise ValueError("give exactly one of model, fields or schema")
        if self.base and self.fields is None:
            raise ValueError("base applies to declarative fields only")
        if (self.core_model is None) != (self.templates.core_document is None):
            raise ValueError("core_model and templates.core_document go together")
        return self


class TemplatesDecl(_Strict):
    """Where a provider's templates are found."""

    directory: str = Field(
        default="templates", description="Template folder, relative to the manifest."
    )


class ProviderManifest(_Strict):
    """A provider's manifest, `chancellor-provider.yaml` or the object an entry point returns.

    One schema for local and plugin providers. Unknown keys are an error.
    """

    api: ManifestApi = Field(alias="_api")
    name: str = Field(
        pattern=r"^[a-z][a-z0-9_-]*(\.[a-z][a-z0-9_-]*)*$",
        description="Provider name; contributions are addressed as `<name>/...`.",
    )
    version: Annotated[str | None, BeforeValidator(_version_text)] = Field(
        default=None,
        description="Provider version. A local provider without one is a degradation.",
    )
    kinds: dict[str, KindDecl] = Field(default_factory=dict)
    templates: TemplatesDecl | None = None
    formatters: dict[str, str] = Field(
        default_factory=dict, description="Formatter types as name: `module:Class`."
    )
    linters: dict[str, str] = Field(
        default_factory=dict, description="Linter types as name: `module:Class`."
    )
    config_loaders: dict[str, str] = Field(
        default_factory=dict, description="Config loaders as name: `module:Class`."
    )
    version_schemes: dict[str, str] = Field(
        default_factory=dict, description="Version schemes as name: `module:Class`."
    )


@dataclass(frozen=True)
class Degradation:
    """A build input chancellor cannot fingerprint reliably."""

    code: str
    subject: str
    message: str


class Provider(ABC):
    """A named, versioned bundle of contributions, loaded from one of three sources."""

    @property
    @abstractmethod
    def manifest(self) -> ProviderManifest:
        """The validated manifest."""

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    @abstractmethod
    def origin(self) -> str:
        """Distribution name, or the provider folder relative to the project root."""

    @property
    @abstractmethod
    def code(self) -> bool:
        """True when fingerprinted by a version string, False when by content digest."""

    @abstractmethod
    def template_root(self) -> Traversable | None:
        """Folder holding the provider's templates, if it contributes any."""

    @abstractmethod
    def import_object(self, reference: str) -> Any:
        """Import `module:attribute` as this provider resolves modules."""

    @abstractmethod
    def fingerprint(self, template_sources: Mapping[str, str]) -> str:
        """Fingerprint of the provider, given its template sources from the loader."""

    def degradations(self) -> list[Degradation]:
        """Reasons this provider cannot be fingerprinted reliably; empty when it can."""
        return []


# Formatters, linters, config loaders


@dataclass(frozen=True)
class FormatContext:
    """Settings a formatter receives from chancellor's configuration."""

    wrap_width: int


class Formatter(BaseModel, ABC):
    """Shapes the rendered body of a document. Fields are the type's config arguments."""

    model_config = ConfigDict(extra="forbid")

    @abstractmethod
    def format(self, text: str, context: FormatContext) -> str:
        """Return the formatted text."""


@dataclass(frozen=True)
class LintContext:
    """What a linter is told about the run."""

    root: Path
    allow_execution: bool = True


@dataclass(frozen=True)
class LintResult:
    """Outcome of a linter run: chancellor records it and trusts neither part."""

    problems: bool
    output: str = ""
    returncode: int = 0


class Linter(BaseModel, ABC):
    """Checks documents. Fields are the type's config arguments."""

    model_config = ConfigDict(extra="forbid")

    @abstractmethod
    def lint(self, paths: Sequence[Path], context: LintContext) -> LintResult:
        """Check `paths` (all documents when empty) and report the result."""


class VersionScheme(BaseModel, ABC):
    """How a project writes and orders versions (0.1.0:D0036): `builtin.semver`, `builtin.pep440`,
    `builtin.free`, or a provider's own, named in `config/<key>/versioning/scheme`.

    `key` parses a version into a sort key, or returns `None` when the text is not a version
    of the scheme. A scheme whose `checks` is false validates and orders nothing; chancellor
    then only compares versions for equality.
    """

    model_config = ConfigDict(extra="forbid")

    checks: ClassVar[bool] = True

    @abstractmethod
    def key(self, text: str) -> Any | None:
        """Sort key of `text`, or `None` if it is not a version of this scheme."""

    def is_version(self, text: str) -> bool:
        """Whether `text` is a version, e.g. the version part of an absolute ID."""
        return self.key(text) is not None

    def compare(self, left: str, right: str) -> int:
        """-1, 0 or 1 as `left` sorts before, equal to or after `right`; both must parse."""
        left_key, right_key = self.key(left), self.key(right)
        return (left_key > right_key) - (left_key < right_key)


@dataclass(frozen=True)
class LoadedConfig:
    """Configuration of one module as a loader found it."""

    data: Mapping[str, Any]
    origin: str
    sources: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LoaderContext:
    """What a config loader is told about the project when chancellor constructs it."""

    root: Path
    data_file: Path | None
    keys: ModuleKeys
    tree: Mapping[str, Any]
    files: tuple[str, ...] = ()


class ConfigLoader(ABC):
    """Delivers chancellor's configuration section (0.1.0:D0004).

    Named in `config/<key>/loaders` by a type address (`builtin.data_file`) or an import path,
    optionally as a mapping whose other keys are passed as `arguments`. Chancellor constructs
    it with the project's `LoaderContext`; loaders listed first take precedence.
    """

    def __init__(self, context: LoaderContext, **arguments: Any) -> None:
        self.context = context
        self.arguments = arguments

    @abstractmethod
    def load(self) -> LoadedConfig:
        """Return the raw configuration mapping and where it came from."""


__all__ = [
    "VersionScheme",
    "Version",
    "VersioningConfig",
    "MetaTree",
    "MetaInfo",
    "section_types",
    "TypeRef",
    "Section",
    "ProviderEntry",
    "ProjectModel",
    "KindTemplatesConfig",
    "KindConfig",
    "ConfigTree",
    "ChancellorConfig",
    "ApiTree",
    "ApiMeta",
    "EXTENSION_POINTS",
    "MANIFEST_FILE",
    "ConfigLoader",
    "CoreModel",
    "Degradation",
    "DigestExclude",
    "FieldDecl",
    "FormatContext",
    "Formatter",
    "Generated",
    "KindDecl",
    "KindTemplates",
    "LintContext",
    "LintResult",
    "Linter",
    "LoadedConfig",
    "LoaderContext",
    "ManifestApi",
    "Model",
    "Origin",
    "Provider",
    "ProviderManifest",
    "RecordIndex",
    "Depends",
    "RecordRef",
    "RecordRefs",
    "RefLink",
    "RootModel",
    "TemplatesDecl",
    "collect_ref_links",
    "collect_refs",
    "marked_fields",
]
