"""A consumer's `kinds` defaults merge per field with provider defaults.

Priority: CLI > environment > data file and loaders > consumer class defaults > provider
defaults > built-in defaults.
"""

import textwrap
from pathlib import Path

import pytest

from chancellor.api import ChancellorConfig, KindConfig, KindTemplatesConfig
from chancellor.build import explain, plan, run
from chancellor.config import config_model, consumer_kind_defaults
from chancellor.errors import ConfigError
from chancellor.project import Project
from chancellor.providers import builtin_providers
from chancellor.registry import Registry

from .conftest import edit

ROOT = """
from pydantic import Field, field_validator
from chancellor.api import ChancellorConfig, ConfigTree, KindConfig, KindTemplatesConfig, ProjectModel
from chancellor.builtin.jkrenzer.models import RequirementSection, SpecificationSection


class MyConfig(ChancellorConfig):
    kinds: dict[str, KindConfig] = Field(default_factory=lambda: {KINDS_HERE})


class MyTree(ConfigTree):
    chancellor: MyConfig = Field(default_factory=MyConfig)


class Root(ProjectModel):
    config: MyTree = Field(default_factory=MyTree)
    requirements: RequirementSection | None = None
    specifications: SpecificationSection | None = None
"""


def supply(project_dir: Path, kinds: str, source: str = ROOT, **config) -> None:
    path = project_dir / "arch" / "models" / "root.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source.replace("KINDS_HERE", kinds)), "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            data_model="arch/models/root.py:Root", **config
        ),
    )


def decision_paths(project: Project) -> set[str]:
    return {d.rel for d in plan(project).documents if d.kind == "decisions"}


def test_consumer_folder_default_is_used_and_shown(project_dir: Path, cli) -> None:
    supply(project_dir, '"decisions": KindConfig(folder="out/dec")')
    assert "out/dec/D0001-yaml-storage.md" in decision_paths(Project.load())
    code, out, _ = cli("schema", "config")
    assert code == 0 and '"default": "out/dec"' in out


def test_partial_override_keeps_the_other_fields(project_dir: Path) -> None:
    supply(project_dir, '"decisions": KindConfig(folder="out/dec")')
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={
                "decisions": {
                    "templates": {"records": "builtin.jkrenzer/requirement.md.j2"}
                }
            }
        ),
    )
    spec = Project.load().registry.kinds["decisions"]
    assert spec.folder == "out/dec"
    assert spec.templates.records == "builtin.jkrenzer/requirement.md.j2"
    assert spec.templates.core_document == "builtin.jkrenzer/decision-core.md.j2"


def test_priority_level_by_level(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def folder(**load) -> str:
        return Project.load(**load).registry.kinds["decisions"].folder

    assert folder() == "arch/decisions"  # provider
    supply(project_dir, '"decisions": KindConfig(folder="consumer")')
    assert folder() == "consumer"
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"decisions": {"folder": "file"}}
        ),
    )
    assert folder() == "file"
    monkeypatch.setenv("CHANCELLOR_KINDS__DECISIONS__FOLDER", "env")
    assert folder() == "env"
    assert folder(overrides={"kinds": {"decisions": {"folder": "cli"}}}) == "cli"


def test_consumer_kind_config_subclass_survives(project_dir: Path) -> None:
    source = ROOT.replace(
        "class MyConfig(ChancellorConfig):",
        """class Owned(KindConfig):
    owner: str = "docs"

    @field_validator("owner")
    @classmethod
    def lower(cls, value):
        if value != value.lower():
            raise ValueError("owner must be lower case")
        return value


class MyConfig(ChancellorConfig):""",
    ).replace("kinds: dict[str, KindConfig]", "kinds: dict[str, Owned]")
    supply(project_dir, '"decisions": Owned(owner="arch")', source)
    project = Project.load()
    assert project.config.kinds.decisions.owner == "arch"
    assert project.config.kinds.requirements.owner == "docs"
    digest = project.config_digest
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"requirements": {"owner": "ops"}}
        ),
    )
    assert Project.load().config_digest != digest
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"requirements": {"owner": "Ops"}}
        ),
    )
    with pytest.raises(ConfigError, match="owner must be lower case"):
        Project.load()


def test_unregistered_kind_default_is_refused(project_dir: Path) -> None:
    supply(project_dir, '"tasks": KindConfig(folder="x")')
    with pytest.raises(
        ConfigError, match="kinds default for tasks, which no provider registers"
    ):
        Project.load()


def test_consumer_data_default_is_honoured(project_dir: Path) -> None:
    from chancellor.yamlio import dump, load  # pylint: disable=import-outside-toplevel

    data = load(project_dir / "chancellor.yaml")
    (project_dir / "arch" / "data").mkdir(parents=True)
    (project_dir / "arch" / "data" / "decisions.yaml").write_text(
        dump(data.pop("decisions")), "utf-8"
    )
    (project_dir / "chancellor.yaml").write_text(dump(data), "utf-8")
    supply(project_dir, '"decisions": KindConfig(data="arch/data/decisions.yaml")')
    assert "arch/decisions/D0001-yaml-storage.md" in decision_paths(Project.load())


def test_changed_consumer_default_moves_the_config_digest(project_dir: Path) -> None:
    supply(project_dir, '"decisions": KindConfig(folder="out/a")')
    run(Project.load())
    supply(project_dir, '"decisions": KindConfig(folder="out/b")')
    assert "config: config/chancellor changed" in "\n".join(
        explain(Project.load(), "R0001")
    )


def test_consumer_model_default_takes_the_override_checks(project_dir: Path) -> None:
    """The same subclass check, fingerprint and data_model clash as config."""
    edit(
        project_dir / "chancellor.yaml",
        lambda d: [r.update(source=["S-1"]) for r in d["decisions"]["records"]],
    )
    supply(project_dir, '"decisions": KindConfig(model="tests.traced:TracedDecision")')
    project = Project.load()
    assert type(project.records["D0001"][1]).__name__ == "TracedDecision"
    assert (
        "model:decisions" in project.model_overrides
        or "decisions" in project.model_overrides
    )
    supply(project_dir, '"decisions": KindConfig(model="tests.traced:NotADecision")')
    with pytest.raises(ConfigError, match="is not a subclass"):
        Project.load()
    supply(
        project_dir, '"requirements": KindConfig(model="tests.traced:TracedDecision")'
    )
    with pytest.raises(ConfigError, match="both say which model validates the data"):
        Project.load()


def test_explicit_built_in_value_wins() -> None:
    """An explicitly set field counts, even at its built-in value."""

    class Explicit(ChancellorConfig):
        kinds: dict[str, KindConfig] = {"decisions": KindConfig(folder=None, data=None)}

    assert consumer_kind_defaults(Explicit) == {
        "decisions": {"folder": None, "data": None}
    }
    model = config_model(Registry.build(builtin_providers()), base=Explicit)
    decisions = (
        model.model_fields["kinds"].annotation.model_fields["decisions"].annotation
    )
    assert (
        decisions.model_fields["folder"].default is None
    )  # explicit beats the provider's

    class Implicit(ChancellorConfig):
        kinds: dict[str, KindConfig] = {
            "decisions": KindConfig(templates=KindTemplatesConfig())
        }

    assert consumer_kind_defaults(Implicit) == {"decisions": {"templates": {}}}
