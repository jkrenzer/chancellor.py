"""Loading a project: layout, configuration, merging, paths, refs, root model (step 4)."""

import os
from pathlib import Path

import pytest

from chancellor.build import plan, render
from chancellor.errors import ConfigError, ExitCode, InputError
from chancellor.keys import ModuleKeys
from chancellor.paths import find_root
from chancellor.project import Project
from chancellor.yamlio import dump, load

from .conftest import edit, record


def input_hashes(directory: Path) -> dict[str, str]:
    return {
        d.rel: d.inputs.input_hash
        for d in plan(Project.load(directory / "chancellor.yaml")).documents
    }


@pytest.mark.usefixtures("project_dir")
def test_sample_loads() -> None:
    project = Project.load()
    assert sorted(project.records) == [
        "D0000",
        "D0001",
        "D0002",
        "R0000",
        "R0001",
        "S0000",
        "S0001",
    ]
    assert [p.name for p in project.registry.providers] == [
        "builtin",
        "builtin.jkrenzer",
    ]


def test_unscoped_layout_is_refused_with_the_new_shape(project_dir: Path) -> None:
    (project_dir / "chancellor.yaml").write_text(
        '_api:\n  version: "1.0.0"\n  kind: architectural_records\ndecisions: {}\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError) as caught:
        Project.load()
    message = str(caught.value)
    assert "unscoped layout" in message and "kind: project_records" in message
    assert "chancellor:" in message


def test_missing_api_is_a_config_error(project_dir: Path) -> None:
    edit(project_dir / "chancellor.yaml", lambda d: d.pop("_api"))
    with pytest.raises(ConfigError, match="missing _api.chancellor"):
        Project.load()


def test_no_data_file_is_a_config_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError, match="No chancellor.yaml"):
        Project.load()
    assert not Project.load(require_data=False).sections


def test_data_file_from_environment(
    project_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path_factory.mktemp("elsewhere"))
    monkeypatch.setenv("CHANCELLOR_DATA", str(project_dir / "chancellor.yaml"))
    assert Project.load().root == project_dir.resolve()


def test_unknown_config_key_suggests_the_nearest(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(wrap_widht=80),
    )
    with pytest.raises(ConfigError) as caught:
        Project.load()
    assert "config.chancellor.wrap_widht" in str(caught.value)
    assert "did you mean wrap_width" in str(caught.value)
    assert "builtin.jkrenzer" in str(caught.value)


def test_unknown_kind_config_key(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"decisions": {"fodler": "x"}}
        ),
    )
    with pytest.raises(ConfigError, match="did you mean folder"):
        Project.load()


@pytest.mark.usefixtures("project_dir")
def test_environment_overrides_config(monkeypatch: pytest.MonkeyPatch) -> None:
    before = Project.load()
    monkeypatch.setenv("CHANCELLOR_WRAP_WIDTH", "72")
    after = Project.load()
    assert after.config.wrap_width == 72 and after.config_digest != before.config_digest


def test_module_keys_are_variable(project_dir: Path) -> None:
    def move(data: dict) -> None:
        data["_api"]["embedded"] = data["_api"].pop("chancellor")
        data["config"]["embedded"] = data["config"].pop("chancellor")

    edit(project_dir / "chancellor.yaml", move)
    with pytest.raises(ConfigError):
        Project.load()
    project = Project.load(keys=ModuleKeys(default="embedded"))
    assert project.config.wrap_width == 100
    partial = ModuleKeys(default="embedded", overrides={"config": "embedded"})
    assert partial.api == "embedded" and partial.providers == "embedded"


def test_other_modules_do_not_move_digests(project_dir: Path) -> None:
    before = input_hashes(project_dir)

    def other(data: dict) -> None:
        data["_api"]["field-marshall"] = {"version": "1.0.0"}
        data["config"]["field-marshall"] = {"calendars": "planning/calendars"}
        data["tasks"] = [{"id": "T0042", "title": "Something else"}]

    edit(project_dir / "chancellor.yaml", other)
    assert input_hashes(project_dir) == before


def test_split_files_change_no_digest(project_dir: Path) -> None:
    before = input_hashes(project_dir)
    data = load(project_dir / "chancellor.yaml")
    data_dir = project_dir / "data"
    data_dir.mkdir()
    (data_dir / "a-decisions.yaml").write_text(
        dump({"decisions": data.pop("decisions")}), "utf-8"
    )
    first = data["requirements"]["records"][:1]
    data["requirements"]["records"] = []
    (data_dir / "b-requirements.yaml").write_text(
        dump({"requirements": {"records": first}}), "utf-8"
    )
    data["config"]["chancellor"]["include"] = ["data"]
    (project_dir / "chancellor.yaml").write_text(dump(data), "utf-8")
    assert input_hashes(project_dir) == before
    project = Project.load()
    assert (
        project.tree.record_origins[("decisions", "D0001")] == "data/a-decisions.yaml"
    )
    assert (
        project.tree.record_origins[("requirements", "R0001")]
        == "data/b-requirements.yaml"
    )


def test_value_defined_in_two_files_names_both(project_dir: Path) -> None:
    (project_dir / "more.yaml").write_text(
        "config:\n  chancellor:\n    wrap_width: 80\n", "utf-8"
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["more.yaml"]),
    )
    with pytest.raises(
        ConfigError,
        match=r"config\.chancellor\.wrap_width is defined in chancellor\.yaml and in more\.yaml",
    ):
        Project.load()


def test_duplicate_id_across_files_names_both(project_dir: Path) -> None:
    data = load(project_dir / "chancellor.yaml")
    copy = {"decisions": {"records": [record(data, "decisions", "D0002")]}}
    (project_dir / "more.yaml").write_text(dump(copy), "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["more.yaml"]),
    )
    with pytest.raises(
        InputError,
        match="Duplicate record ID D0002 in decisions: in chancellor.yaml and more.yaml",
    ):
        Project.load()


def test_providers_only_in_main_file(project_dir: Path) -> None:
    (project_dir / "more.yaml").write_text(
        "config:\n  chancellor:\n    providers: [{name: x, path: x}]\n", "utf-8"
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["more.yaml"]),
    )
    with pytest.raises(ConfigError, match="main data file"):
        Project.load()


def test_invalid_record_reports_location(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").pop("context"),
    )
    with pytest.raises(
        InputError, match=r"decisions\.records\[1\]\.context: Field required"
    ):
        Project.load()


def test_dangling_ref_fails_external_ref_passes(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(
            addresses=["ISO-9001", "R0009"]
        ),
    )
    with pytest.raises(
        InputError, match="decisions.D0002: reference R0009 names no record"
    ) as caught:
        Project.load()
    assert "<project>:<version>:<id> (other-project:1.0.0:D0001) or a URL" in str(
        caught.value
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(addresses=["ISO-9001"]),
    )
    Project.load()


def test_folder_must_stay_inside_root(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={"decisions": {"folder": "../out"}}
        ),
    )
    with pytest.raises(ConfigError, match="outside the project root"):
        plan(Project.load())


@pytest.mark.skipif(os.name == "nt", reason="symlinks need privileges on Windows")
def test_symlink_escaping_root_is_refused(
    project_dir: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    (project_dir / "arch").mkdir()
    (project_dir / "arch" / "decisions").symlink_to(outside)
    with pytest.raises(ConfigError, match="outside the project root"):
        plan(Project.load())


def test_root_detection(tmp_path: Path) -> None:
    nested = tmp_path / "repo" / "docs"
    nested.mkdir(parents=True)
    data = nested / "chancellor.yaml"
    data.write_text("", "utf-8")
    assert find_root(data) == nested
    (tmp_path / "repo" / ".git").mkdir()
    assert find_root(data) == tmp_path / "repo"
    (nested / "pyproject.toml").write_text("", "utf-8")
    assert find_root(data) == nested


def test_root_detection_prefers_the_nearest_marker(tmp_path: Path) -> None:
    """A pyproject.toml above the repository must not take the root out of it."""
    repo = tmp_path / "outer" / "repo"
    (repo / ".git").mkdir(parents=True)
    (tmp_path / "outer" / "pyproject.toml").write_text("", "utf-8")
    data = repo / "chancellor.yaml"
    data.write_text("", "utf-8")
    assert find_root(data) == repo


def test_root_model_and_folders_combine(project_dir: Path) -> None:
    """Output folders are not blocked by a supplied root model."""
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            data_model="tests.rootmodel:Catalogue",
            kinds={"decisions": {"folder": "out"}},
        ),
    )
    paths = {d.rel for d in plan(Project.load()).documents}
    assert "out/D0001-yaml-storage.md" in paths


def test_root_model_renders_the_same_bytes(project_dir: Path) -> None:
    generated = Project.load()
    built = plan(generated)
    expected = {d.rel: render(generated, d, built) for d in built.documents}
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            data_model="tests.rootmodel:Catalogue"
        ),
    )
    supplied = Project.load()
    assert supplied.root_model is not None
    built = plan(supplied)
    assert {d.rel: render(supplied, d, built) for d in built.documents} == expected


def test_record_data_defined_twice_is_an_input_error(project_dir: Path) -> None:
    """Record data defined in two files is invalid input (exit 2), not configuration."""
    (project_dir / "more.yaml").write_text(
        "decisions:\n  core:\n    title: Another title\n", "utf-8"
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["more.yaml"]),
    )
    with pytest.raises(
        InputError,
        match=r"decisions\.core\.title is defined in chancellor\.yaml and in more\.yaml",
    ):
        Project.load()


def test_every_section_is_logged_at_info(
    project_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Unknown sections are not degradations, but `-v` shows every section and its fate."""
    edit(project_dir / "chancellor.yaml", lambda d: d.update(decision={"records": []}))
    with caplog.at_level("INFO", logger="chancellor"):
        Project.load()
    messages = [r.getMessage() for r in caplog.records]
    assert any(
        m.startswith("section decisions: kind of provider builtin.jkrenzer")
        for m in messages
    )
    assert any(
        m.startswith("section decision: no registered kind, ignored") for m in messages
    )


def test_kind_data_file_changes_no_digest(project_dir: Path) -> None:
    """A kind's records may live in a data file; file layout is not content."""
    before = input_hashes(project_dir)
    data = load(project_dir / "chancellor.yaml")
    (project_dir / "arch" / "data").mkdir(parents=True)
    (project_dir / "arch" / "data" / "decisions.yaml").write_text(
        dump(data.pop("decisions")), "utf-8"
    )
    data["config"]["chancellor"]["kinds"] = {
        "decisions": {"data": "arch/data/decisions.yaml"}
    }
    (project_dir / "chancellor.yaml").write_text(dump(data), "utf-8")
    assert input_hashes(project_dir) == before
    project = Project.load()
    assert (
        project.tree.record_origins[("decisions", "D0001")]
        == "arch/data/decisions.yaml"
    )


def test_kind_data_file_rules(
    project_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    def configure(path: str, include: list[str] | None = None) -> None:
        def change(d: dict) -> None:
            d.pop("decisions", None)
            record(d, "requirements", "R0001")["addressed_by"] = ["S0001"]
            d["config"]["chancellor"]["kinds"] = {"decisions": {"data": path}}
            if include is not None:
                d["config"]["chancellor"]["include"] = include

        edit(project_dir / "chancellor.yaml", change)

    configure("arch/data/decisions.yaml")
    with caplog.at_level("INFO", logger="chancellor"):
        project = Project.load()
    assert "decisions" not in project.sections  # missing file: no data yet
    assert any("does not exist yet" in r.getMessage() for r in caplog.records)
    folder = project_dir / "arch" / "data"
    folder.mkdir(parents=True)
    (folder / "decisions.yaml").write_text("- not a mapping\n", "utf-8")
    with pytest.raises(InputError, match="must hold a mapping with core and records"):
        Project.load()
    (folder / "decisions.yaml").write_text("records: []\n", "utf-8")
    configure("arch/data/decisions.yaml", include=["arch/data/decisions.yaml"])
    with pytest.raises(ConfigError, match="also read as a whole data tree"):
        Project.load()
    configure("../decisions.yaml")
    with pytest.raises(ConfigError, match="outside the project root"):
        Project.load()


def test_data_location_walks_a_key_path(project_dir: Path) -> None:
    """The shared-file case (future, 0.1.0:D0019) only needs `location_for` to fill the key path."""
    from chancellor.datatree import (  # pylint: disable=import-outside-toplevel
        DataLocation,
        merge_kind_data,
    )

    data = load(project_dir / "chancellor.yaml")
    shared = {"records": {"decisions": data.pop("decisions")}}
    record(data, "requirements", "R0001")["addressed_by"] = ["S0001"]
    (project_dir / "shared.yaml").write_text(dump(shared), "utf-8")
    (project_dir / "other.yaml").write_text(dump({"records": {}}), "utf-8")
    (project_dir / "chancellor.yaml").write_text(dump(data), "utf-8")
    project = Project.load()
    assert "decisions" not in project.sections
    merge_kind_data(
        project.tree,
        project.root,
        "decisions",
        DataLocation("shared.yaml", ("records", "decisions")),
    )
    assert len(project.tree.data["decisions"]["records"]) == 2
    with pytest.raises(InputError, match="has no key records.missing"):
        merge_kind_data(
            project.tree,
            project.root,
            "requirements",
            DataLocation("other.yaml", ("records", "missing")),
        )


def test_two_kinds_cannot_share_a_data_file_yet(project_dir: Path) -> None:
    """A shared file needs a key path per kind, which is a later extension."""
    folder = project_dir / "arch" / "data"
    folder.mkdir(parents=True)
    (folder / "both.yaml").write_text("records: []\n", "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            kinds={
                "decisions": {"data": "arch/data/both.yaml"},
                "requirements": {"data": "arch/data/both.yaml"},
            }
        ),
    )
    with pytest.raises(ConfigError, match="already the data file of decisions"):
        Project.load()


def test_missing_data_file_never_deletes_documents(project_dir: Path, cli) -> None:
    """A misspelt kind data path is "no data yet", but existing documents are kept, reported
    as orphans, and the build degrades so --strict fails."""
    data = load(project_dir / "chancellor.yaml")
    folder = project_dir / "arch" / "data"
    folder.mkdir(parents=True)
    (folder / "decisions.yaml").write_text(dump(data.pop("decisions")), "utf-8")
    data["config"]["chancellor"]["kinds"] = {
        "decisions": {"data": "arch/data/decisions.yaml"}
    }
    (project_dir / "chancellor.yaml").write_text(dump(data), "utf-8")
    assert cli("build")[0] == 0
    edit(
        project_dir / "chancellor.yaml",
        lambda d: (
            d["config"]["chancellor"].update(
                kinds={"decisions": {"data": "arch/data/decision.yaml"}}
            ),
            record(d, "requirements", "R0001").update(addressed_by=["S0001"]),
        ),
    )
    code, out, err = cli("build", "--strict")
    assert code == ExitCode.DEGRADED
    assert "orphan\tarch/decisions/D0001-yaml-storage.md" in out
    assert "missing-data-file" in err and "kept, not deleted" in err
    assert (project_dir / "arch/decisions/D0001-yaml-storage.md").is_file()
