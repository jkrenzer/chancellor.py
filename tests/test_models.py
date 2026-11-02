"""Behaviour of the builtin.jkrenzer models: the authoring contract carried over from the
render script, re-specified against chancellor's API."""

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from chancellor.api import CoreModel, Model
from chancellor.builtin.jkrenzer import models
from chancellor.doctor import undescribed_fields
from chancellor.errors import InputError
from chancellor.hashing import data_hash
from chancellor.providers import builtin_providers
from chancellor.registry import Registry

REVISION = {"version": "1.0.0", "date": "2026-10-26", "description": "Initial record."}

BASE = {
    "title": "Full Title",
    "description": "What it covers.",
    "author": "author",
    "state": "drafted",
    "revisions": [REVISION],
}
RECORD = {**BASE, "context": "Background."}

INPUTS: dict[type[Model], dict[str, Any]] = {
    models.Decision: {
        **RECORD,
        "id": "D0001",
        "decision": ["Do it."],
        "consequences": ["Fine."],
    },
    models.Requirement: {
        **RECORD,
        "id": "R0001",
        "requirement": ["Must."],
        "goals": ["Goal."],
        "stakeholders": ["Users."],
        "responsibility": ["Team."],
    },
    models.Specification: {
        **RECORD,
        "id": "S0001",
        "subject": ["Artifact."],
        "terms": ["Term: meaning."],
        "specification": [{"designation": "Clause", "statements": ["Statement."]}],
        "conformance": ["Check."],
    },
    models.DecisionCore: {
        **BASE,
        "id": "D0000",
        "introduction": "Intro.",
        "rule_sets": [{"scope": "Scope:", "rules": ["Rule."]}],
    },
}
INPUTS[models.RequirementCore] = {**INPUTS[models.DecisionCore], "id": "R0000"}
INPUTS[models.SpecificationCore] = {**INPUTS[models.DecisionCore], "id": "S0000"}

RECORD_MODELS = [models.Decision, models.Requirement, models.Specification]
ALL_MODELS = list(INPUTS)


def valid(model: type[Model], **changes: Any) -> dict[str, Any]:
    data = copy.deepcopy(INPUTS[model])
    data.update(changes)
    return data


def errors(model: type[Model], data: dict[str, Any]) -> str:
    with pytest.raises(ValidationError) as caught:
        model.model_validate(data)
    return str(InputError.from_validation(caught.value, model))


@pytest.mark.parametrize("model", ALL_MODELS)
def test_minimal_input_is_valid_and_derived_values_are_filled(
    model: type[Model],
) -> None:
    record = model.model_validate(valid(model))
    assert record.short_title == "Full Title"
    assert str(record.date) == "2026-10-26"
    assert record.version == "1.0.0"


@pytest.mark.parametrize("model", ALL_MODELS)
def test_every_violation_is_reported(model: type[Model]) -> None:
    data = valid(model)
    del data["title"]
    data["author"] = "  "
    message = errors(model, data)
    assert "- title: Field required" in message
    assert "- author: must contain non-whitespace text" in message


@pytest.mark.parametrize("model", ALL_MODELS)
@pytest.mark.parametrize("value", [None, "", "   ", []])
def test_required_text_rejects_empty(model: type[Model], value: Any) -> None:
    errors(model, valid(model, description=value))


@pytest.mark.parametrize("model", RECORD_MODELS)
@pytest.mark.parametrize("value", [None, "", "  "])
def test_optional_text_omitted_null_blank_mean_not_given(
    model: type[Model], value: Any
) -> None:
    record = model.model_validate(valid(model, notes=value, short_title=value))
    assert record.notes is None and record.short_title == "Full Title"


@pytest.mark.parametrize("model", RECORD_MODELS)
def test_null_lists_mean_empty(model: type[Model]) -> None:
    record = model.model_validate(valid(model, tags=None, references=None))
    assert record.tags == [] and record.references == []


@pytest.mark.parametrize("model", ALL_MODELS)
@pytest.mark.parametrize("legacy", ["status", "short", "version", "data_hash"])
def test_unknown_and_legacy_inputs_fail(model: type[Model], legacy: str) -> None:
    assert f"{legacy}: Extra inputs are not permitted" in errors(
        model, valid(model, **{legacy: "x"})
    )


def test_inputs_of_another_kind_fail() -> None:
    errors(models.Decision, valid(models.Decision, goals=["x"]))
    errors(models.Requirement, valid(models.Requirement, decision=["x"]))


@pytest.mark.parametrize("field", ["version", "date", "description"])
def test_incomplete_revision_fails(field: str) -> None:
    revision = {k: v for k, v in REVISION.items() if k != field}
    errors(models.Decision, valid(models.Decision, revisions=[revision]))


def test_unordered_and_duplicate_revisions_fail() -> None:
    later = {**REVISION, "version": "1.1.0", "date": "2026-10-27"}
    assert "oldest first" in errors(
        models.Decision, valid(models.Decision, revisions=[later, REVISION])
    )
    same = {**later, "version": "1.0.0"}
    assert "unique" in errors(
        models.Decision, valid(models.Decision, revisions=[REVISION, same])
    )


def test_last_revision_gives_version_and_first_the_date() -> None:
    later = {**REVISION, "version": "2.0.0", "date": "2026-11-01"}
    record = models.Decision.model_validate(
        valid(models.Decision, revisions=[REVISION, later])
    )
    assert record.version == "2.0.0" and str(record.date) == "2026-10-26"


def test_tags_strings_and_mappings() -> None:
    record = models.Decision.model_validate(
        valid(models.Decision, tags=["a", {"area": "x"}])
    )
    assert record.tags == ["a", {"area": "x"}]


@pytest.mark.parametrize("tag", ["", {}, {"k": ""}, {"": "v"}, 3, ["a"]])
def test_malformed_tags_fail(tag: Any) -> None:
    errors(models.Decision, valid(models.Decision, tags=[tag]))


@pytest.mark.parametrize(
    "reference",
    [
        {},
        {"designation": ""},
        {"designation": "x", "pointers": [""]},
        {"designation": "x", "y": 1},
    ],
)
def test_malformed_references_fail(reference: Any) -> None:
    errors(models.Decision, valid(models.Decision, references=[reference]))


def test_blank_reference_description_defaults_without_mutating_input() -> None:
    data = valid(models.Decision, references=[{"designation": "x", "description": " "}])
    before = copy.deepcopy(data)
    record = models.Decision.model_validate(data)
    assert record.references[0].description is None
    assert data == before


@pytest.mark.parametrize(
    "clause",
    [
        {},
        {"designation": "x"},
        {"designation": "x", "statements": []},
        {"designation": "x", "statements": [" "]},
    ],
)
def test_malformed_clauses_fail(clause: Any) -> None:
    errors(models.Specification, valid(models.Specification, specification=[clause]))


@pytest.mark.parametrize(
    "ids",
    [
        ("D0000", models.Decision),
        ("D0001", models.DecisionCore),
        ("X0001", models.Decision),
    ],
)
def test_id_patterns(ids: tuple[str, type[Model]]) -> None:
    record_id, model = ids
    if model is models.Decision:
        assert models.Decision.model_validate(valid(model, id="D0000")).id == "D0000"
        errors(models.Decision, valid(model, id="X0001"))
    else:
        errors(model, valid(model, id=record_id))


def test_core_model_without_index_records_cannot_be_instantiated() -> None:
    """The abstract hook is enforced; Pydantic's metaclass derives from ABCMeta."""

    class Incomplete(CoreModel):  # pylint: disable=abstract-method
        pass

    with pytest.raises(TypeError, match="abstract"):
        Incomplete(id="X0000")
    with pytest.raises(TypeError, match="abstract"):
        Incomplete.model_validate({"id": "X0000"})


def test_core_index_is_generated_not_input() -> None:
    message = errors(models.DecisionCore, valid(models.DecisionCore, records=[]))
    assert "records generated by chancellor" in message


@pytest.mark.parametrize("key", ["context", "references", "notes", "addresses"])
def test_core_rejects_record_inputs(key: str) -> None:
    errors(models.DecisionCore, valid(models.DecisionCore, **{key: "x"}))


def test_every_field_of_every_registered_kind_is_described() -> None:
    """Walks every registered kind's models, nested models included."""
    assert not undescribed_fields(Registry.build(builtin_providers()))


def test_hash_ignores_input_form_but_not_content() -> None:
    implicit = models.Decision.model_validate(valid(models.Decision))
    explicit = models.Decision.model_validate(
        valid(
            models.Decision,
            short_title="Full Title",
            date="2026-10-26",
            tags=[],
            notes=None,
            alternatives=[],
            references=[],
            addresses=None,
        )
    )
    assert data_hash(implicit) == data_hash(explicit)
    changed = models.Decision.model_validate(valid(models.Decision, context="Other."))
    assert data_hash(changed) != data_hash(implicit)


def test_core_hash_ignores_its_generated_index() -> None:
    core = models.DecisionCore.model_validate(valid(models.DecisionCore))
    decision = models.Decision.model_validate(valid(models.Decision))
    assert data_hash(core.index_records([decision])) == data_hash(core)


def test_refs_are_indexed() -> None:
    record = models.Decision.model_validate(
        valid(models.Decision, addresses=["R0001", "EXT-1"])
    )
    assert record.model_index().refs == ("R0001", "EXT-1")


def test_markers_travel_into_the_schema() -> None:
    schema = str(models.DecisionCore.model_json_schema()) + str(
        models.Decision.model_json_schema()
    )
    assert "x-chancellor-generated" in schema and "x-chancellor-record-ref" in schema


def test_model_save_drops_generated_and_computed_fields() -> None:
    core = models.DecisionCore.model_validate(valid(models.DecisionCore))
    decision = models.Decision.model_validate(valid(models.Decision))
    saved = core.index_records([decision]).model_save()
    assert "records" not in saved and "version" not in saved
    assert models.DecisionCore.model_validate(saved) == core
