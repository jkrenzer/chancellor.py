"""Supplied root models built from chancellor's public bases (0.1.0:D0030): every field and default
is inherited, config included."""

import json
import textwrap
from pathlib import Path

import pytest

from chancellor.api import ProjectModel, Section
from chancellor.build import explain, plan, render, run
from chancellor.config import config_model
from chancellor.errors import ConfigError, InputError
from chancellor.keys import ModuleKeys
from chancellor.project import Project, config_class
from chancellor.providers import builtin_providers
from chancellor.registry import Registry

from .conftest import edit, record

SECTIONS = """
from chancellor.api import ProjectModel
from chancellor.builtin.jkrenzer.models import (
    DecisionSection, RequirementSection, SpecificationSection,
)


class Catalogue(ProjectModel):
    decisions: DecisionSection | None = None
    requirements: RequirementSection | None = None
    specifications: SpecificationSection | None = None
"""

CONFIG = SECTIONS + """

from pydantic import Field, field_validator
from chancellor.api import ChancellorConfig, ConfigTree


class MyConfig(ChancellorConfig):
    wrap_width: int = 80
    team: str = Field(default="docs", description="A project field of our own.")

    @field_validator("team")
    @classmethod
    def lower(cls, value: str) -> str:
        if value != value.lower():
            raise ValueError("team must be lower case")
        return value


class MyConfigTree(ConfigTree):
    chancellor: MyConfig = Field(default_factory=MyConfig)


class Configured(Catalogue):
    config: MyConfigTree = Field(default_factory=MyConfigTree)
"""


def supply(project_dir: Path, source: str, reference: str, **config) -> None:
    path = project_dir / "arch" / "models" / "root.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            data_model=f"arch/models/root.py:{reference}", **config
        ),
    )


def rendered(project: Project) -> dict[str, str]:
    built = plan(project)
    return {d.rel: render(project, d, built) for d in built.documents}


def test_generated_models_use_the_public_bases() -> None:
    """No privileged path for the generated models."""
    registry = Registry.build(builtin_providers())
    assert issubclass(registry.root_model(), ProjectModel)
    assert issubclass(registry.section_model("decisions"), Section)


def test_section_only_root_model_renders_the_same_bytes(project_dir: Path) -> None:
    expected = rendered(Project.load())
    supply(project_dir, SECTIONS, "Catalogue")
    project = Project.load()
    assert project.root_model is not None
    assert rendered(project) == expected


def test_config_defaults_inherit_with_file_and_environment_winning(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].pop("wrap_width"),
    )
    supply(project_dir, CONFIG, "Configured")
    assert Project.load().config.wrap_width == 80  # the class default
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(wrap_width=90),
    )
    assert Project.load().config.wrap_width == 90  # the file wins
    monkeypatch.setenv("CHANCELLOR_WRAP_WIDTH", "70")
    assert Project.load().config.wrap_width == 70  # the environment wins


def test_added_field_and_validator_survive(project_dir: Path, cli) -> None:
    """The merged model is built on top of the consumer's subclass."""
    supply(project_dir, CONFIG, "Configured")
    project = Project.load()
    assert project.config.team == "docs"
    digest = project.config_digest
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(team="ops"),
    )
    assert Project.load().config_digest != digest
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(team="Ops"),
    )
    with pytest.raises(ConfigError, match="team must be lower case"):
        Project.load()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(team="ops"),
    )
    code, out, _ = cli("schema", "config")
    schema = json.loads(out)
    assert code == 0 and "team" in schema["properties"]
    assert schema["properties"]["wrap_width"]["default"] == 80


def test_changed_class_default_rebuilds_everything(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].pop("wrap_width"),
    )
    supply(project_dir, CONFIG, "Configured")
    run(Project.load())
    path = project_dir / "arch" / "models" / "root.py"
    path.write_text(
        path.read_text("utf-8").replace("wrap_width: int = 80", "wrap_width: int = 72"),
        "utf-8",
    )
    assert "config: config/chancellor changed" in "\n".join(
        explain(Project.load(), "D0001")
    )


def test_override_exclusive_only_for_declared_kinds(project_dir: Path) -> None:
    only_requirements = """
from chancellor.api import ProjectModel
from chancellor.builtin.jkrenzer.models import RequirementSection


class Partial(ProjectModel):
    requirements: RequirementSection | None = None
"""
    supply(
        project_dir,
        only_requirements,
        "Partial",
        kinds={"requirements": {"model": "tests.traced:TracedDecision"}},
    )
    with pytest.raises(
        ConfigError, match="data_model and config.chancellor.kinds.requirements.model"
    ):
        Project.load()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: (
            d["config"]["chancellor"].update(
                kinds={"decisions": {"model": "tests.traced:TracedDecision"}}
            ),
            [r.update(source=["item-42"]) for r in d["decisions"]["records"]],
        ),
    )
    assert type(Project.load().records["D0001"][1]).__name__ == "TracedDecision"


def test_section_with_foreign_record_model_is_refused(project_dir: Path) -> None:
    foreign = """
from chancellor.api import ProjectModel, Section
from chancellor.builtin.jkrenzer.models import Decision, RequirementCore


class Wrong(ProjectModel):
    requirements: Section[RequirementCore, Decision] | None = None
"""
    supply(project_dir, foreign, "Wrong")
    with pytest.raises(
        ConfigError, match="field requirements: records of Decision are not a subclass"
    ):
        Project.load()


def test_config_error_exits_1_record_error_exits_2(project_dir: Path) -> None:
    supply(project_dir, CONFIG, "Configured")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").pop("author"),
    )
    with pytest.raises(InputError, match="author"):
        Project.load()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: (
            record(d, "decisions", "D0002").update(author="x"),
            d["config"]["chancellor"].update(team="Ops"),
        ),
    )
    with pytest.raises(ConfigError):
        Project.load()


def test_protocol_root_model_still_works_with_a_log(
    project_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            data_model="tests.rootmodel:Catalogue"
        ),
    )
    with caplog.at_level("INFO", logger="chancellor"):
        Project.load()
    assert any(
        "does not inherit chancellor.api.ProjectModel" in r.getMessage()
        for r in caplog.records
    )


def test_schema_data_includes_api_and_config(project_dir: Path, cli) -> None:
    supply(project_dir, SECTIONS, "Catalogue")
    code, out, _ = cli("schema", "data")
    properties = json.loads(out)["properties"]
    assert code == 0 and {"_api", "config", "decisions"} <= set(properties)


def test_module_key_alias_moves_config(tmp_path: Path) -> None:
    source = textwrap.dedent(CONFIG) + """

class EmbeddedTree(ConfigTree):
    chancellor: MyConfig = Field(default_factory=MyConfig, alias="embedded")


class Embedded(Catalogue):
    config: EmbeddedTree = Field(default_factory=EmbeddedTree)
"""
    namespace: dict = {}
    exec(compile(source, "embedded.py", "exec"), namespace)  # pylint: disable=exec-used
    assert (
        config_class(namespace["Embedded"], ModuleKeys(default="embedded")).__name__
        == "MyConfig"
    )
    assert (
        config_class(namespace["Embedded"], ModuleKeys()).__name__ == "ChancellorConfig"
    )
    del tmp_path


def test_merged_model_extends_the_consumer_class() -> None:
    from chancellor.api import (  # pylint: disable=import-outside-toplevel
        ChancellorConfig,
    )

    class Mine(ChancellorConfig):
        extra_flag: bool = True

    model = config_model(Registry.build(builtin_providers()), base=Mine)
    assert (
        issubclass(model, Mine)
        and "decisions" in model.model_fields["kinds"].annotation.model_fields
    )
