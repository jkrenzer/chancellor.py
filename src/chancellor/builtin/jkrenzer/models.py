"""Record models of the `builtin.jkrenzer` flavour: decisions, requirements, specifications.

Every kind has ordinary records and one core document that introduces the kind's folder,
states its rules and indexes its records. The models are the single source of truth for the
accepted inputs; their field descriptions are written for human authors and AI agents alike.

Validation is strict on purpose. Missing required values, blank text, wrong types, unknown
input names and malformed nested entries fail instead of being repaired. Optional values that
are omitted, null or blank fall back to their documented default. Derived values — the short
title, the creation date, the version — are filled in here, never in a template.
"""

from collections.abc import Sequence
from datetime import date as Date
from typing import Annotated, Any, ClassVar, Self, TypeAlias

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from chancellor.api import CoreModel, Generated, Model, RecordRefs, Section, Version


def _require_content(value: str) -> str:
    if not value.strip():
        raise ValueError("must contain non-whitespace text")
    return value


def _blank_to_none(value: Any) -> Any:
    return None if isinstance(value, str) and not value.strip() else value


def _none_to_empty(value: Any) -> Any:
    return [] if value is None else value


Text: TypeAlias = Annotated[str, Field(min_length=1), AfterValidator(_require_content)]
"""Nonempty text that contains at least one non-whitespace character."""

OptionalText: TypeAlias = Annotated[str | None, BeforeValidator(_blank_to_none)]
"""Optional text; omitted, null and blank values all mean "not given"."""

OptionalDate: TypeAlias = Annotated[Date | None, BeforeValidator(_blank_to_none)]
"""Optional ISO date; omitted, null and blank values all mean "not given"."""

TextList: TypeAlias = Annotated[list[Text], Field(min_length=1)]
"""Nonempty list of nonempty text items."""

OptionalTextList: TypeAlias = Annotated[list[Text], BeforeValidator(_none_to_empty)]
"""List of nonempty text items; omitted or null means an empty list."""

Tag: TypeAlias = Text | Annotated[dict[Text, Text], Field(min_length=1)]
"""A plain tag, or a nonempty mapping of keys to values such as `{"area": "storage"}`."""

Tags: TypeAlias = Annotated[list[Tag], BeforeValidator(_none_to_empty)]


def file_name(record_id: str, label: str, suffix: str = ".md") -> str:
    """`<id>-<kebab-case label><suffix>`, the file name the folder rules require."""
    words = "".join(c if c.isalnum() else " " for c in label.lower()).split()
    return "-".join([record_id, *words]) + suffix


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Revision(_Strict):
    """One entry of a record's revision history; the last one gives the record version."""

    version: Annotated[Text, Version()] = Field(
        examples=["1.0.0"],
        description=(
            "Version string of this revision, unique within the record. Quote it in "
            'YAML ("1.0.0") so it stays a string.'
        ),
    )
    date: Date = Field(
        examples=["2026-10-26"], description="Date of this revision as `YYYY-MM-DD`."
    )
    description: Text = Field(
        examples=["Initial record."],
        description="Short summary of what this revision changed.",
    )


class Reference(_Strict):
    """A source or related record listed under References and Links."""

    designation: Text = Field(
        examples=["Addressed requirements"],
        description="Name of the reference, rendered in bold.",
    )
    description: OptionalText = Field(
        default=None,
        description=(
            "Optional explanation of why the reference is relevant. "
            "Omitted, null or blank renders nothing."
        ),
    )
    pointers: OptionalTextList = Field(
        default_factory=list,
        examples=[["[D0001: Adopt ADR and ARR](D0001-adopt-adr-and-arr.md)"]],
        description=(
            "Where the reference is found: Markdown links, bibliographic citations or "
            "precise text locations. Each pointer renders as a sub-item."
        ),
    )


class Clause(_Strict):
    """A group of normative statements inside a specification.

    A clause renders as a level-three heading, its optional description and its statements.
    Cite a single statement by the clause designation and its position within the clause.
    """

    designation: Text = Field(
        examples=["Device fields"],
        description="Heading of the clause; it identifies the clause for citations.",
    )
    description: OptionalText = Field(
        default=None,
        description=(
            "Optional explanatory prose shown before the statements. It is not normative. "
            "Schema fragments go here as fenced code blocks."
        ),
    )
    statements: TextList = Field(
        description=(
            "Normative statements of the clause, one per item. An explanatory sub-bullet "
            'inside a statement begins with "Note:" or "Example:".'
        ),
    )


class RuleSet(_Strict):
    """Rules of a core document that apply to one scope, such as the files of the folder."""

    scope: Text = Field(
        examples=["Following rules are to be applied to the files in this folder:"],
        description=(
            "Sentence introducing the rules and naming what they apply to. It renders "
            "verbatim as the paragraph before the list."
        ),
    )
    rules: TextList = Field(description="The rules of this scope, one per item.")


class IndexEntry(_Strict):
    """One record listed in the index of its kind's core document, generated by chancellor."""

    id: str = Field(description="ID of the listed record.")
    short_title: str = Field(description="Short title of the listed record.")
    description: str = Field(description="Description of the listed record.")
    tags: list[Tag] = Field(
        default_factory=list, description="Tags of the listed record."
    )
    file_name: str = Field(
        description="File name of the listed record within the folder."
    )


class Document(Model):
    """Fields shared by every record and core document of this flavour."""

    front_matter: ClassVar[tuple[str, ...] | None] = (
        "title",
        "id",
        "short_title",
        "description",
        "tags",
        "author",
        "date",
        "state",
        "version",
        "revisions",
    )

    title: Text = Field(
        description="Full, descriptive and specific title of the record."
    )
    id: Text = Field(description="Record identifier; the pattern depends on the kind.")
    short_title: OptionalText = Field(
        default=None,
        description="Short label used in links and in the file name. Defaults to `title`.",
    )
    description: Text = Field(
        description=(
            "What the record covers, in plain Markdown prose. The core document of the "
            "kind lists it in its index, so keep it informative on its own."
        ),
    )
    tags: Tags = Field(
        default_factory=list,
        examples=[["storage", {"area": "architecture"}]],
        description=(
            "Keywords for finding and grouping records, each a nonempty string or a "
            "nonempty mapping of string keys to string values. Omitted or null means no "
            "tags."
        ),
    )
    author: Text = Field(description="Name or role of the author.")
    date: OptionalDate = Field(
        default=None,
        description="Creation date as `YYYY-MM-DD`. Defaults to the first revision's date.",
    )
    state: Text = Field(
        examples=["drafted", "accepted"],
        description=(
            "Explicit lifecycle state of the record. It is never inferred, so it must always "
            "be given."
        ),
    )
    revisions: list[Revision] = Field(
        min_length=1,
        description=(
            "Revision history, oldest first, with unique versions. The last entry determines "
            "the record version."
        ),
    )

    @field_validator("revisions")
    @classmethod
    def _revisions_ordered_and_unique(cls, revisions: list[Revision]) -> list[Revision]:
        dates = [revision.date for revision in revisions]
        if dates != sorted(dates):
            raise ValueError("revisions must be ordered oldest first")
        versions = [revision.version for revision in revisions]
        if len(versions) != len(set(versions)):
            raise ValueError("revision versions must be unique")
        return revisions

    @model_validator(mode="after")
    def _fill_derived_defaults(self) -> Self:
        if self.short_title is None:
            self.short_title = self.title
        if self.date is None:
            self.date = self.revisions[0].date
        return self

    @computed_field(description="Version of the last revision.")
    @property
    def version(self) -> str:
        return self.revisions[-1].version

    def output_name(self, suffix: str) -> str:
        return file_name(self.id, self.short_title or self.title, suffix)


class Record(Document):
    """Fields shared by decisions, requirements and specifications.

    Write clear, concise and objective Markdown. Support factual claims with references and
    label assumptions, proposals and unresolved questions explicitly; do not invent evidence,
    targets or agreement.
    """

    context: Text = Field(
        description=(
            "Markdown background: the problem, its origin and the constraints that apply. "
            "Keep normative content and decisions out of it."
        ),
    )
    references: Annotated[list[Reference], BeforeValidator(_none_to_empty)] = Field(
        default_factory=list,
        description='Sources and related records. Omitted or null renders "None.".',
    )
    notes: OptionalText = Field(
        default=None,
        description=(
            "Supplementary or administrative Markdown, such as unresolved questions. "
            'Omitted, null or blank renders "None.".'
        ),
    )

    def index_entry(self, suffix: str) -> IndexEntry:
        return IndexEntry(
            id=self.id,
            short_title=self.short_title or self.title,
            description=self.description,
            tags=self.tags,
            file_name=self.output_name(suffix),
        )


def _with_link(front_matter: tuple[str, ...] | None, link: str) -> tuple[str, ...]:
    keys = list(front_matter or ())
    keys.insert(keys.index("id") + 1, link)
    return tuple(keys)


class Decision(Record):
    """Architectural Decision Record (ADR): a choice, its alternatives and consequences.

    Cover one decision per record. Give an unfamiliar reader enough information to
    understand and later reassess the decision.
    """

    front_matter = _with_link(Document.front_matter, "addresses")
    inverse_refs = {"addresses": "addressed_by"}

    id: Annotated[str, Field(pattern=r"^D\d{4}$")] = Field(
        examples=["D0003"], description="Decision identifier `D####`."
    )
    addresses: RecordRefs = Field(
        default_factory=list,
        examples=[["R0001"]],
        description=(
            "Requirements this decision addresses, as `R####` IDs or explicit external "
            "identifiers. Each listed requirement lists this decision in `addressed_by`."
        ),
    )
    decision: TextList = Field(
        description=(
            "The chosen approach, its scope and its main reasons, one decision point per "
            "item. Items may contain nested Markdown sub-bullets."
        ),
    )
    alternatives: OptionalTextList = Field(
        default_factory=list,
        description=(
            "Alternatives actually evaluated, with benefits, drawbacks, rejection or deferral "
            "reasons and conditions for reconsideration. Empty means no evaluation was "
            "documented, not that no alternative exists; do not invent one."
        ),
    )
    consequences: TextList = Field(
        description=(
            "Positive and negative effects of the chosen decision, including maintenance "
            "costs and affected stakeholders where known."
        ),
    )


class Requirement(Record):
    """Architectural Requirement Record (ARR): a need, its goals and its owners.

    Cover one requirement per record. A requirement may exist before any decision or
    specification addresses it.
    """

    front_matter = _with_link(Document.front_matter, "addressed_by")
    inverse_refs = {"addressed_by": "addresses"}

    id: Annotated[str, Field(pattern=r"^R\d{4}$")] = Field(
        examples=["R0002"], description="Requirement identifier `R####`."
    )
    addressed_by: RecordRefs = Field(
        default_factory=list,
        examples=[["D0001"]],
        description=(
            "Decisions (`D####`) and specifications (`S####`) that address this requirement, "
            "or explicit external identifiers. Keep it consistent with their `addresses`."
        ),
    )
    requirement: TextList = Field(
        description=(
            "What must be achieved and under which conditions, one obligation per item. Make "
            "fulfillment verifiable where possible and prescribe an implementation only when "
            "that implementation is itself required."
        ),
    )
    goals: TextList = Field(
        description=(
            "Intended outcomes as short items, each one developable into a goal that meets "
            "SMARTER and PURE goal criteria. Name unresolved conflicts."
        ),
    )
    stakeholders: TextList = Field(
        description=(
            "Affected people or groups and their relevant interests or impact. This is "
            "distinct from accountability under `responsibility`."
        ),
    )
    responsibility: TextList = Field(
        description=(
            "Who owns the requirement, resolves questions and approves changes. Use an "
            "accountable role or group where a named person is not appropriate."
        ),
    )


class Specification(Record):
    """Architectural Specification Record (ASR): what an artifact is.

    Every clause statement is normative and all remaining text is explanatory. Keep the need
    in the addressed requirement and the reasoning in the governing decision, and link that
    decision under `references`. The kind's core document states the content rules.
    """

    front_matter = _with_link(Document.front_matter, "addresses")
    inverse_refs = {"addresses": "addressed_by"}

    id: Annotated[str, Field(pattern=r"^S\d{4}$")] = Field(
        examples=["S0001"], description="Specification identifier `S####`."
    )
    addresses: RecordRefs = Field(
        default_factory=list,
        examples=[["R0001"]],
        description=(
            "Requirements this specification answers, as `R####` IDs or explicit external "
            "identifiers. Each listed requirement lists this specification in "
            "`addressed_by`."
        ),
    )
    subject: TextList = Field(
        description=(
            "Delimits the specified artifact: the parts this record binds and, stated "
            "explicitly as exclusions, related parts it does not."
        ),
    )
    terms: TextList = Field(
        description=(
            "Every term the normative statements rely on, each item giving the term and its "
            "definition. Do not define terms inside a clause."
        ),
    )
    specification: Annotated[list[Clause], Field(min_length=1)] = Field(
        description="The normative content, grouped into clauses.",
    )
    conformance: TextList = Field(
        description=(
            "How an artifact is checked against the clauses: the check, the evidence it "
            "produces and the clause it covers. Record a statement that cannot be checked yet "
            "as such instead of implying a verification."
        ),
    )


class CoreDocument(Document, CoreModel):
    """Core document of a kind: its introduction, rules and generated index of records."""

    introduction: Text = Field(
        description="Markdown introduction: what the folder documents and how.",
    )
    rule_sets: Annotated[list[RuleSet], Field(min_length=1)] = Field(
        description="Rules applying to the folder, grouped by the scope they apply to.",
    )
    records: Annotated[list[IndexEntry], Generated()] = Field(
        default_factory=list,
        description=(
            "Index of the kind's records, generated by chancellor from the records' own "
            "data; not an input."
        ),
    )

    def index_records(self, records: Sequence[Model], *, suffix: str = ".md") -> Self:
        entries = [
            record.index_entry(suffix)
            for record in sorted(records, key=lambda record: record.id)
            if isinstance(record, Record)
        ]
        return self.model_copy(update={"records": entries})


class DecisionCore(CoreDocument):
    """Core document of the decisions (`D0000`): rules and index of decisions."""

    id: Annotated[str, Field(pattern=r"^D0000$")] = Field(
        examples=["D0000"], description="Identifier of the decision core, `D0000`."
    )


class RequirementCore(CoreDocument):
    """Core document of the requirements (`R0000`): rules and index of requirements."""

    id: Annotated[str, Field(pattern=r"^R0000$")] = Field(
        examples=["R0000"], description="Identifier of the requirement core, `R0000`."
    )


class SpecificationCore(CoreDocument):
    """Core document of the specifications (`S0000`): rules and index of specifications."""

    id: Annotated[str, Field(pattern=r"^S0000$")] = Field(
        examples=["S0000"], description="Identifier of the specification core, `S0000`."
    )


class DecisionSection(Section[DecisionCore, Decision]):
    """The decisions' section of a root model: core document `D0000` and decision records."""

    core: DecisionCore = Field(description="The decisions' core document.")


class RequirementSection(Section[RequirementCore, Requirement]):
    """The requirements' section of a root model: core document `R0000` and requirements."""

    core: RequirementCore = Field(description="The requirements' core document.")


class SpecificationSection(Section[SpecificationCore, Specification]):
    """The specifications' section of a root model: core document `S0000` and specifications."""

    core: SpecificationCore = Field(description="The specifications' core document.")
