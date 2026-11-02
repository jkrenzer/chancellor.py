"""References declare what flows over them: `RecordRef(depends=...)` (0.1.0:D0032)."""

import json
from pathlib import Path

import pytest

from chancellor.build import plan, render, run
from chancellor.errors import ConfigError
from chancellor.project import Project

from .conftest import edit, record
from .test_providers import MANIFEST, add_provider, override_decision_template


def manifest(depends: str) -> str:
    """The test provider's manifest, its `partners` refs declaring `depends`."""
    return MANIFEST.replace(
        'partners: {type: "list[record_ref]", required: false}',
        f'partners: {{type: "list[record_ref]", required: false, depends: {depends}}}',
    )


def input_hash(rel: str) -> str:
    lock = json.loads(Path("chancellor.lock").read_text("utf-8"))
    return lock["documents"][rel]["input_hash"]


def rebuilds(change) -> bool:
    """Whether I0001's document moves when `change` is applied."""
    run(Project.load())
    before = input_hash("arch/interface/I0001.md")
    change()
    run(Project.load())
    return input_hash("arch/interface/I0001.md") != before


def interface(partners: list[str]) -> list[dict]:
    return [{"id": "I0001", "title": "Bus", "protocol": "CAN", "partners": partners}]


def test_name_flow_gives_a_link_and_rebuilds_on_rename_only(project_dir: Path) -> None:
    template = "{% for p in refs.partners %}[{{ p.id }}]({{ p.path }})\n{% endfor %}"
    add_provider(
        project_dir, manifest("name"), template, interfaces=interface(["D0001"])
    )
    project = Project.load()
    built = plan(project)
    text = render(project, next(d for d in built.documents if d.id == "I0001"), built)
    assert text == "[D0001](arch/decisions/D0001-yaml-storage.md)\n"
    data = project_dir / "chancellor.yaml"
    assert not rebuilds(
        lambda: edit(data, lambda d: record(d, "decisions", "D0001").update(state="x"))
    )
    assert rebuilds(
        lambda: edit(
            data, lambda d: record(d, "decisions", "D0001").update(short_title="Y")
        )
    )


def test_data_flow_reads_the_target_and_rebuilds_on_its_data(project_dir: Path) -> None:
    template = "{% for p in refs.partners %}{{ p.data.title }}/{{ p.data.state }}\n{% endfor %}"
    add_provider(
        project_dir, manifest("data"), template, interfaces=interface(["D0001"])
    )
    project = Project.load()
    built = plan(project)
    text = render(project, next(d for d in built.documents if d.id == "I0001"), built)
    assert text == "Store the Sample Data as YAML/accepted\n"
    data = project_dir / "chancellor.yaml"
    assert rebuilds(
        lambda: edit(data, lambda d: record(d, "decisions", "D0001").update(state="x"))
    )


def test_data_flow_reaches_one_hop_only(project_dir: Path) -> None:
    """The target's own references are IDs in its data; nothing further is exposed."""
    add_provider(
        project_dir,
        manifest("data"),
        "{{ refs.partners[0].data.title }}\n",
        interfaces=interface(["D0001"]),
    )
    data = project_dir / "chancellor.yaml"
    assert not rebuilds(
        lambda: edit(
            data, lambda d: record(d, "requirements", "R0001").update(state="x")
        )
    )


def test_id_flow_target_change_does_not_rebuild(project_dir: Path) -> None:
    add_provider(
        project_dir,
        manifest("id"),
        "{{ refs.partners | map(attribute='id') | join(',') }}\n",
        interfaces=interface(["D0001"]),
    )
    data = project_dir / "chancellor.yaml"
    assert not rebuilds(
        lambda: edit(data, lambda d: record(d, "decisions", "D0001").update(state="x"))
    )


@pytest.mark.parametrize(
    "template",
    [
        "{{ refs.partners[0].data.title }}\n",
        "{{ refs.partners[0].file_name }}\n",
        '{% import "extprov/_reach.md.j2" as r %}{{ r.reach(refs) }}\n',
    ],
)
def test_template_cannot_reach_past_an_id_flow(
    project_dir: Path, template: str
) -> None:
    """Through direct use, a macro, and a local template override alike."""
    folder = add_provider(
        project_dir, manifest("id"), template, interfaces=interface(["D0001"])
    )
    (folder / "templates" / "_reach.md.j2").write_text(
        "{% macro reach(refs) %}{{ refs.partners[0].data.title }}{% endmacro %}",
        "utf-8",
    )
    with pytest.raises(ConfigError, match="template extprov/interface.md.j2"):
        run(Project.load())


def test_overriding_builtin_template_cannot_read_address_targets(
    project_dir: Path,
) -> None:
    folder = add_provider(project_dir, manifest("id"), "x\n", interfaces=[])
    (folder / "templates" / "decision.md.j2").write_text(
        "{{ refs.addresses[0].data.title }}\n", "utf-8"
    )
    override_decision_template(project_dir, "extprov/decision.md.j2")
    with pytest.raises(ConfigError, match="has no attribute 'data'"):
        run(Project.load())


CORE = '''
from typing import Annotated

from chancellor.api import Generated
from chancellor.builtin.jkrenzer.models import DecisionCore


class StatefulCore(DecisionCore):
    """A core whose index context also shows each record's state."""

    states: Annotated[list[str], Generated()] = []

    def index_records(self, records, *, suffix=".md"):
        indexed = super().index_records(records, suffix=suffix)
        return indexed.model_copy(update={"states": [r.state for r in records]})
'''


def test_core_refs_part_is_exactly_its_index_context(project_dir: Path) -> None:
    """Add a field to the index context, and the core's part moves with it."""
    data = project_dir / "chancellor.yaml"
    run(Project.load())
    before = input_hash("arch/decisions/D0000-decision-core.md")
    edit(data, lambda d: record(d, "decisions", "D0002").update(state="x"))
    run(Project.load())
    assert (
        input_hash("arch/decisions/D0000-decision-core.md") == before
    )  # state not shown
    module = project_dir / "arch" / "models" / "core.py"
    module.parent.mkdir(parents=True)
    module.write_text(CORE, "utf-8")
    edit(
        data,
        lambda d: d["config"]["chancellor"].update(
            kinds={"decisions": {"core_model": "arch/models/core.py:StatefulCore"}}
        ),
    )
    run(Project.load())
    before = input_hash("arch/decisions/D0000-decision-core.md")
    edit(data, lambda d: record(d, "decisions", "D0002").update(state="y"))
    run(Project.load())
    assert input_hash("arch/decisions/D0000-decision-core.md") != before


def test_depends_travels_into_the_schema(project_dir: Path) -> None:
    add_provider(project_dir, manifest("name"), "x\n", interfaces=interface([]))
    schema = Project.load().registry.kinds["interface"].model.model_json_schema()
    assert (
        schema["properties"]["partners"]["items"]["x-chancellor-record-ref"] == "name"
    )


def test_reserved_context_names(project_dir: Path) -> None:
    title = "      title: {type: text}\n"
    bad = manifest("id").replace(
        title, title + "      refs: {type: str, required: false}\n"
    )
    add_provider(project_dir, bad, "x\n", interfaces=[])
    with pytest.raises(
        ConfigError, match="field refs is reserved in the template context"
    ):
        Project.load()


def test_reaching_past_one_hop_names_cause_and_fix(project_dir: Path) -> None:
    """References inside a target's data are IDs; the error says so and how to fix it."""
    template = "{{ refs.partners[0].data.addresses[0].data.title }}\n"
    add_provider(
        project_dir, manifest("data"), template, interfaces=interface(["D0001"])
    )
    with pytest.raises(ConfigError) as caught:
        run(Project.load())
    message = str(caught.value)
    assert (
        "data references reach one hop (chains of references are not followed yet)"
        in message
    )
    assert "refs.<field>" in message


@pytest.mark.parametrize(
    ("template", "wanted"),
    [
        ("{{ refs.partners[0].data.title }}\n", 'depends="data"'),
        ("{{ refs.partners[0].path }}\n", 'depends="name"'),
    ],
)
def test_reading_past_the_declared_flow_names_the_fix(
    project_dir: Path, template: str, wanted: str
) -> None:
    add_provider(project_dir, manifest("id"), template, interfaces=interface(["D0001"]))
    with pytest.raises(ConfigError, match=f"declare `{wanted}` on the field"):
        run(Project.load())
