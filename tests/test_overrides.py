"""Config model overrides: `kinds.<kind>.model` and `core_model` (0.1.0:D0025)."""

import json
import textwrap
from pathlib import Path

import pytest

from chancellor.build import explain, plan, render, run
from chancellor.errors import ConfigError, InputError
from chancellor.hashing import data_hash
from chancellor.project import Project
from chancellor.yamlio import parse

from .conftest import edit, record

MODELS = """
# A project file naming the subclasses; they are defined once in tests/traced.py.
from tests.traced import TracedCore, TracedDecision

__all__ = ["TracedCore", "TracedDecision"]
"""


def override(project_dir: Path, models: str = MODELS, **kinds: str) -> Path:
    path = project_dir / "arch" / "models" / "records.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(models), "utf-8")

    def change(data: dict) -> None:
        data["config"]["chancellor"]["kinds"] = {"decisions": kinds}
        for item in data["decisions"]["records"]:
            item["source"] = ["item-57"]

    edit(project_dir / "chancellor.yaml", change)
    return path


def document(project: Project, record_id: str) -> str:
    built = plan(project)
    return render(project, next(d for d in built.documents if d.id == record_id), built)


def test_file_override_adds_a_field_and_front_matter(project_dir: Path) -> None:
    override(project_dir, model="arch/models/records.py:TracedDecision")
    project = Project.load()
    assert type(project.records["D0001"][1]).__name__ == "TracedDecision"
    header = parse(document(project, "D0001").split("---\n")[1], "front matter")
    assert list(header)[5:8] == ["tags", "source", "author"]
    assert header["source"] == ["item-57"]


def test_override_field_is_validated(project_dir: Path) -> None:
    override(project_dir, model="arch/models/records.py:TracedDecision")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").pop("source"),
    )
    with pytest.raises(
        InputError, match=r"decisions\.records\[1\]\.source: Field required"
    ):
        Project.load()


def test_module_override(project_dir: Path) -> None:
    override(project_dir, model="tests.traced:TracedDecision")
    assert type(Project.load().records["D0001"][1]).__name__ == "TracedDecision"


def test_core_model_override(project_dir: Path) -> None:
    override(
        project_dir,
        model="arch/models/records.py:TracedDecision",
        core_model="arch/models/records.py:TracedCore",
    )
    assert type(Project.load().records["D0000"][1]).__name__ == "TracedCore"


@pytest.mark.parametrize(
    ("reference", "message"),
    [
        (
            "tests.traced:NotADecision",
            "is not a subclass of chancellor.builtin.jkrenzer.models.Decision",
        ),
        ("arch/models/missing.py:TracedDecision", "missing.py does not exist"),
        ("arch/models/records.py:Nope", "has no Nope"),
        ("no.such.module:X", "cannot import no.such.module"),
        ("../outside.py:X", "outside the project root"),
        ("TracedDecision", "must be written path/to/file.py:Name or module:Name"),
    ],
)
def test_bad_override_is_a_config_error(
    project_dir: Path, reference: str, message: str
) -> None:
    override(project_dir, model=reference)
    with pytest.raises(ConfigError) as caught:
        Project.load()
    assert "config.chancellor.kinds.decisions.model" in str(caught.value)
    assert message in str(caught.value)


def test_override_and_data_model_are_exclusive(project_dir: Path) -> None:
    override(project_dir, model="arch/models/records.py:TracedDecision")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            data_model="tests.rootmodel:Catalogue"
        ),
    )
    with pytest.raises(
        ConfigError, match="data_model and config.chancellor.kinds.decisions.model"
    ):
        Project.load()


def test_schema_reflects_the_override(project_dir: Path, cli) -> None:
    override(project_dir, model="arch/models/records.py:TracedDecision")
    for name in ("adr", "decisions", "data"):
        code, out, _ = cli("schema", name)
        assert code == 0 and '"source"' in out
    code, out, _ = cli("schema", "config")
    assert code == 0 and '"core_model"' in json.dumps(json.loads(out))
    code, out, _ = cli("providers")
    assert out.splitlines()[-1].startswith(
        "model:decisions\tarch/models/records.py\tcode\tc1:sha256:"
    )


def test_override_code_change_rebuilds_everything(project_dir: Path) -> None:
    """An override's code fingerprint is part of the whole-set providers part."""
    path = override(project_dir, model="arch/models/records.py:TracedDecision")
    run(Project.load())
    before = json.loads((project_dir / "chancellor.lock").read_text("utf-8"))[
        "documents"
    ]
    # A validator changes no schema, so only the code fingerprint can notice it.
    path.write_text(
        path.read_text("utf-8") + textwrap.dedent("""

        class Checked(TracedDecision):
            pass
        """),
        "utf-8",
    )
    message = "\n".join(explain(Project.load(), "D0001"))
    assert "providers: model override of kind decisions" in message
    run(Project.load())
    after = json.loads((project_dir / "chancellor.lock").read_text("utf-8"))[
        "documents"
    ]
    moved = {
        rel for rel in after if after[rel]["input_hash"] != before[rel]["input_hash"]
    }
    assert moved == set(after)


def test_override_keeps_data_hash_of_shared_fields_meaningful(
    project_dir: Path,
) -> None:
    override(project_dir, model="arch/models/records.py:TracedDecision")
    first = Project.load().records["D0001"][1]
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0001").update(source=["item-58"]),
    )
    second = Project.load().records["D0001"][1]
    assert data_hash(first) != data_hash(second)
