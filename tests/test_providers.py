"""Providers: local kinds, code contributions, fingerprints and degradations."""

import textwrap
from pathlib import Path

import pytest

from chancellor.build import plan, render
from chancellor.config import config_model
from chancellor.errors import ConfigError
from chancellor.project import Project
from chancellor.providers import builtin_providers
from chancellor.registry import Registry

from .conftest import edit

MANIFEST = """\
_api:
  version: 1.0.0
  kind: chancellor_provider
name: extprov
version: 3
kinds:
  interface:
    folder: arch/interface
    templates:
      records: extprov/interface.md.j2
    fields:
      title: {type: text}
      protocol: {type: str, required: true, description: Wire protocol.}
      partners: {type: "list[record_ref]", required: false}
templates:
  directory: templates
"""

TEMPLATE = (
    "# {{ id }}: {{ title }}\n\nProtocol: {{ protocol }}\n"
    "{% for p in partners %}\n- {{ p }}\n{% endfor %}\n"
)


def add_provider(
    project_dir: Path,
    manifest: str = MANIFEST,
    template: str = TEMPLATE,
    interfaces: list | None = None,
) -> Path:
    folder = project_dir / "arch" / "providers" / "extprov"
    (folder / "templates").mkdir(parents=True, exist_ok=True)
    (folder / "chancellor-provider.yaml").write_text(manifest, "utf-8")
    (folder / "templates" / "interface.md.j2").write_text(template, "utf-8")

    def change(data: dict) -> None:
        data["config"]["chancellor"]["providers"] = [
            {"name": "extprov", "path": "arch/providers/extprov"}
        ]
        data["interface"] = {
            "records": (
                interfaces
                if interfaces is not None
                else [
                    {
                        "id": "I0001",
                        "title": "Bus",
                        "protocol": "CAN",
                        "partners": ["D0001"],
                    }
                ]
            )
        }

    edit(project_dir / "chancellor.yaml", change)
    return folder


def override_decision_template(project_dir: Path, address: str) -> None:
    """Point the decisions' records template at `address`, without the interface section."""

    def change(data: dict) -> None:
        data.pop("interface", None)
        data["config"]["chancellor"]["kinds"] = {
            "decisions": {"templates": {"records": address}}
        }

    edit(project_dir / "chancellor.yaml", change)


def test_local_provider_adds_a_kind(project_dir: Path) -> None:
    add_provider(project_dir)
    project = Project.load()
    assert [p.name for p in project.registry.providers][-1] == "extprov"
    built = plan(project)
    document = next(d for d in built.documents if d.id == "I0001")
    assert document.rel == "arch/interface/I0001.md"
    assert (
        render(project, document, built) == "# I0001: Bus\n\nProtocol: CAN\n\n- D0001\n"
    )


def test_declared_fields_validate(project_dir: Path) -> None:
    add_provider(
        project_dir, interfaces=[{"id": "I0001", "title": " ", "protocol": "CAN"}]
    )
    with pytest.raises(Exception, match="title"):
        Project.load()


def test_local_kind_refs_must_resolve(project_dir: Path) -> None:
    add_provider(
        project_dir,
        interfaces=[
            {"id": "I0001", "title": "Bus", "protocol": "CAN", "partners": ["D0009"]}
        ],
    )
    with pytest.raises(Exception, match="D0009 names no record"):
        Project.load()


def test_config_schema_reflects_the_provider_set(project_dir: Path) -> None:
    assert "interface" not in str(
        config_model(Project.load().registry).model_json_schema()
    )
    add_provider(project_dir)
    schema = config_model(Project.load().registry).model_json_schema()
    assert "interface" in str(schema) and "arch/interface" in str(schema)


def test_template_override_through_config(project_dir: Path) -> None:
    folder = add_provider(project_dir)
    (folder / "templates" / "decision.md.j2").write_text("Custom {{ id }}\n", "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"decisions": {"templates": {"records": "extprov/decision.md.j2"}}}
        ),
    )
    project = Project.load()
    built = plan(project)
    document = next(d for d in built.documents if d.id == "D0001")
    assert render(project, document, built).endswith("Custom D0001\n")


def test_missing_override_template_is_a_config_error(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"decisions": {"templates": {"records": "project/decision.md.j2"}}}
        ),
    )
    with pytest.raises(ConfigError, match="names no provider with templates"):
        Project.load()


def test_unknown_manifest_key_names_the_extension_points(project_dir: Path) -> None:
    add_provider(project_dir, MANIFEST + "validators: {}\n")
    with pytest.raises(ConfigError) as caught:
        Project.load()
    assert "validators" in str(caught.value) and "kinds, templates, formatters" in str(
        caught.value
    )


def test_redefining_a_kind_is_an_error(project_dir: Path) -> None:
    manifest = MANIFEST.replace("  interface:", "  decisions:")
    add_provider(project_dir, manifest)
    with pytest.raises(ConfigError, match="already defined by builtin.jkrenzer"):
        Project.load()


def test_declared_but_missing_provider(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            providers=[{"name": "ghost", "path": "arch/providers/ghost"}]
        ),
    )
    with pytest.raises(ConfigError, match="ghost is declared in config"):
        Project.load()


def test_manifest_name_must_match_config(project_dir: Path) -> None:
    add_provider(project_dir, MANIFEST.replace("name: extprov", "name: other"))
    with pytest.raises(ConfigError, match="names itself other"):
        Project.load()


def test_builtin_takes_the_same_path_as_local() -> None:
    registry = Registry.build(builtin_providers())
    assert set(registry.kinds) == {"decisions", "requirements", "specifications"}
    assert registry.lookup("adr-core")[1] == "core_document"
    assert registry.lookup("asr")[0].name == "specifications"
    assert registry.kinds["specifications"].folder == "arch/specification"


def test_declarative_fingerprint_follows_content(project_dir: Path) -> None:
    folder = add_provider(project_dir)
    first = Project.load().registry.fingerprints()["extprov"]
    (folder / "templates" / "interface.md.j2").write_text(TEMPLATE + "\n", "utf-8")
    second = Project.load().registry.fingerprints()["extprov"]
    assert first != second and first.startswith("c1:sha256:")


def test_unversioned_but_fully_hashed_provider_is_only_logged(
    project_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """No degradation while the content can be hashed safely, an INFO message instead."""
    add_provider(project_dir, MANIFEST.replace("version: 3\n", ""))
    with caplog.at_level("INFO", logger="chancellor"):
        project = Project.load()
    assert "extprov" not in {d.subject for d in project.degradations}
    assert any(
        "provider extprov has no version" in r.getMessage() for r in caplog.records
    )


def test_loose_module_model_and_linter(project_dir: Path) -> None:
    head, rest = MANIFEST.split("    fields:\n")
    templates = rest.index("templates:\n  directory")
    manifest = (
        head
        + "    model: models:Interface\n"
        + rest[templates:]
        + "linters:\n  strict: models:FailingLinter\n"
    )
    folder = add_provider(project_dir, manifest)
    (folder / "models.py").write_text(
        textwrap.dedent("""
        from chancellor.api import LintResult, Linter, Model, RecordRefs

        class Interface(Model):
            title: str
            protocol: str
            partners: RecordRefs = []

        class FailingLinter(Linter):
            message: str = "bad"

            def lint(self, paths, context):
                return LintResult(problems=True, output=self.message, returncode=1)
        """),
        "utf-8",
    )
    project = Project.load()
    assert (
        project.registry.type_for("linters", "extprov.strict").__name__
        == "FailingLinter"
    )
    # a module from the provider folder is fingerprinted by its bytes, no degradation.
    assert "extprov" not in {d.subject for d in project.degradations}
    fingerprint = project.registry.fingerprints()["extprov"]
    (folder / "models.py").write_text(
        (folder / "models.py").read_text("utf-8") + "\n# edited\n", "utf-8"
    )
    assert Project.load().registry.fingerprints()["extprov"] != fingerprint


def test_core_index_links_follow_the_records_template_suffix(project_dir: Path) -> None:
    """A records template with another suffix must not leave `.md` links in the index."""
    folder = add_provider(project_dir, interfaces=[])
    (folder / "templates" / "decision.txt.j2").write_text("{{ id }}\n", "utf-8")
    override_decision_template(project_dir, "extprov/decision.txt.j2")
    project = Project.load()
    built = plan(project)
    paths = {d.rel for d in built.documents}
    assert "arch/decisions/D0001-yaml-storage.txt" in paths
    core = render(project, next(d for d in built.documents if d.id == "D0000"), built)
    assert "(D0001-yaml-storage.txt)" in core and "(D0001-yaml-storage.md)" not in core


def test_doctor_notes_undescribed_declared_fields(project_dir: Path, cli) -> None:
    """A declarative field without description is reported for every registered kind."""
    add_provider(project_dir)
    code, out, _ = cli("doctor")
    assert code == 0
    assert "field without description: interface.InterfaceRecord.title" in out
    assert "InterfaceRecord.protocol" not in out  # it has a description
