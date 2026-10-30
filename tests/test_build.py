"""Incremental build, lock and explain."""

import json
from pathlib import Path

import pytest

from chancellor.build import explain, run
from chancellor.errors import ExitCode
from chancellor.hashing import data_hash
from chancellor.project import Project

from .conftest import edit, record
from .test_providers import TEMPLATE, add_provider


def build(check: bool = False):
    return run(Project.load(), check=check)


def rebuilt(result) -> set[str]:
    """Documents whose bytes on disk changed (or would change)."""
    return {rel for rel, status in result.statuses if status != "unchanged"}


def input_hashes() -> dict[str, str]:
    lock = json.loads(Path("chancellor.lock").read_text("utf-8"))
    return {rel: entry["input_hash"] for rel, entry in lock["documents"].items()}


def moved(change) -> set[str]:
    """Documents whose input hash moves when `change` is applied and the project rebuilt."""
    before = input_hashes()
    change()
    build()
    after = input_hashes()
    return {rel for rel in after if before.get(rel) != after[rel]}


def outputs(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted((directory / "arch").rglob("*.md"))
    }


def explained(record_id: str) -> str:
    return "\n".join(explain(Project.load(), record_id))


ALL = {
    "arch/decisions/D0000-decision-core.md",
    "arch/decisions/D0001-yaml-storage.md",
    "arch/decisions/D0002-render-documents-without-network-access.md",
    "arch/requirements/R0000-requirement-core.md",
    "arch/requirements/R0001-reviewable-data.md",
    "arch/specification/S0000-specification-core.md",
    "arch/specification/S0001-data-file-format.md",
}


def test_first_build_writes_everything_second_nothing(project_dir: Path) -> None:
    first = build()
    assert rebuilt(first) == ALL and first.lock_changed
    assert (project_dir / "chancellor.lock").is_file()
    second = build()
    assert rebuilt(second) == set() and not second.lock_changed
    assert not build(check=True).drift


def test_cold_lock_equals_incremental(project_dir: Path) -> None:
    build()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(state="accepted"),
    )
    build()
    incremental = outputs(project_dir)
    lock = (project_dir / "chancellor.lock").read_text("utf-8")
    (project_dir / "chancellor.lock").unlink()
    for path in (project_dir / "arch").rglob("*.md"):
        path.unlink()
    build()
    assert outputs(project_dir) == incremental
    assert (project_dir / "chancellor.lock").read_text("utf-8") == lock


def test_change_rebuilds_only_what_can_flow_over_references(project_dir: Path) -> None:
    """Only changes that can flow over a reference rebuild the referrer."""
    build()
    path = project_dir / "chancellor.yaml"
    # R0001's state is shown nowhere but in its own document: D0001 and S0001 hold its ID only
    # (depends="id"), and R0000's index shows ID, short title, description and tags.
    assert moved(
        lambda: edit(
            path, lambda d: record(d, "requirements", "R0001").update(state="revised")
        )
    ) == {"arch/requirements/R0001-reviewable-data.md"}
    # A new short title renames R0001's file and changes R0000's index entry, nothing else.
    result_paths = moved(
        lambda: edit(
            path,
            lambda d: record(d, "requirements", "R0001").update(
                short_title="Reviewable"
            ),
        )
    )
    assert result_paths == {
        "arch/requirements/R0001-reviewable.md",
        "arch/requirements/R0000-requirement-core.md",
    }


def test_check_reports_drift_and_writes_nothing(project_dir: Path) -> None:
    build()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(state="x"),
    )
    before = outputs(project_dir)
    result = build(check=True)
    assert (
        result.drift
        and "arch/decisions/D0002-render-documents-without-network-access.md"
        in rebuilt(result)
    )
    assert outputs(project_dir) == before


def test_config_change_rebuilds_everything_and_explain_names_it(
    project_dir: Path,
) -> None:
    build()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(wrap_width=60),
    )
    assert "config: config/chancellor changed" in explained("D0001")
    assert rebuilt(build()) >= {"arch/decisions/D0001-yaml-storage.md"}
    assert (
        moved(
            lambda: edit(
                project_dir / "chancellor.yaml",
                lambda d: d["config"]["chancellor"].update(wrap_width=70),
            )
        )
        == ALL
    )


def test_layout_only_config_change_rebuilds_nothing(project_dir: Path) -> None:
    build()
    (project_dir / "empty.yaml").write_text("{}\n", "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["empty.yaml"]),
    )
    assert rebuilt(build()) == set()


def test_other_module_change_rebuilds_nothing(project_dir: Path) -> None:
    build()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"].update({"field-marshall": {"x": 1}}),
    )
    result = build()
    assert rebuilt(result) == set() and not result.lock_changed


def test_local_kind_change_rebuilds_everything_and_names_the_provider(
    project_dir: Path,
) -> None:
    """A provider change rebuilds everything; explain names the provider."""
    folder = add_provider(project_dir)
    build()
    manifest = folder / "chancellor-provider.yaml"
    manifest.write_text(
        manifest.read_text("utf-8").replace(
            "description: Wire protocol.", "description: Bus protocol."
        ),
        "utf-8",
    )
    message = explained("D0001")  # not even of that provider's kind
    assert "providers: provider extprov" in message
    assert "provider set changed" not in message
    manifest.write_text(
        manifest.read_text("utf-8").replace("Bus protocol.", "Wire protocol."), "utf-8"
    )
    assert moved(
        lambda: manifest.write_text(
            manifest.read_text("utf-8").replace("Wire protocol.", "Bus protocol."),
            "utf-8",
        )
    ) == ALL | {"arch/interface/I0001.md"}


def test_provider_template_change_rebuilds_its_documents(project_dir: Path) -> None:
    folder = add_provider(project_dir)
    build()
    (folder / "templates" / "interface.md.j2").write_text(
        TEMPLATE + "\nEnd.\n", "utf-8"
    )
    assert "templates: a template it uses changed" in explained("I0001")
    assert rebuilt(build()) == {"arch/interface/I0001.md"}


def test_provider_set_change_rebuilds_everything(project_dir: Path) -> None:
    build()
    add_provider(project_dir, interfaces=[])
    assert "the provider set changed" in explained("D0001")
    before = input_hashes()
    build()
    after = input_hashes()
    assert all(before[rel] != after[rel] for rel in ALL)


def test_external_edit_is_rendered_again(project_dir: Path) -> None:
    build()
    path = project_dir / "arch/decisions/D0001-yaml-storage.md"
    original = path.read_bytes()
    path.write_text("edited\n", "utf-8")
    result = build()
    assert ("arch/decisions/D0001-yaml-storage.md", "modified") in result.statuses
    assert path.read_bytes() == original


def test_renamed_record_removes_its_old_document(project_dir: Path) -> None:
    build()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(short_title="Offline"),
    )
    result = build()
    assert (
        "arch/decisions/D0002-render-documents-without-network-access.md",
        "removed",
    ) in result.statuses
    assert ("arch/decisions/D0002-offline.md", "new") in result.statuses
    assert not (
        project_dir / "arch/decisions/D0002-render-documents-without-network-access.md"
    ).exists()


def test_edited_orphan_is_left_alone(project_dir: Path) -> None:
    build()
    old = (
        project_dir / "arch/decisions/D0002-render-documents-without-network-access.md"
    )
    old.write_text("mine now\n", "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(short_title="Offline"),
    )
    assert (old.relative_to(project_dir).as_posix(), "orphan") in build().statuses
    assert old.read_text("utf-8") == "mine now\n"


@pytest.mark.parametrize("damage", ["garbage", "old-api", "unknown-tag"])
def test_unusable_lock_is_ignored_and_rebuilt(project_dir: Path, damage: str) -> None:
    build()
    lock_path = project_dir / "chancellor.lock"
    if damage == "garbage":
        lock_path.write_text("not json", "utf-8")
    else:
        data = json.loads(lock_path.read_text("utf-8"))
        if damage == "old-api":
            data["_api"]["version"] = "0"
        else:
            for entry in data["documents"].values():
                entry["output"] = entry["output"].replace("c1:", "c2:")
        lock_path.write_text(json.dumps(data), "utf-8")
    before = outputs(project_dir)
    result = build()
    assert result.lock_changed
    assert outputs(project_dir) == before


def test_lock_records_providers_and_degradations(project_dir: Path) -> None:
    build()
    lock = json.loads((project_dir / "chancellor.lock").read_text("utf-8"))
    assert [p["name"] for p in lock["providers"]] == ["builtin", "builtin.jkrenzer"]
    assert lock["providers"][1]["kinds"] == [
        "decisions",
        "requirements",
        "specifications",
    ]
    entry = lock["documents"]["arch/decisions/D0001-yaml-storage.md"]
    assert set(entry["parts"]) == {
        "data",
        "refs",
        "files",
        "templates",
        "meta",
        "config",
        "api",
        "providers",
    }
    assert entry["sources"] == ["chancellor.yaml"]
    assert all(value.startswith("c1:sha256:") for value in entry["parts"].values())


def test_data_hash_is_the_records_own(project_dir: Path) -> None:
    build()
    project = Project.load()
    text = (project_dir / "arch/decisions/D0001-yaml-storage.md").read_text("utf-8")
    assert f"data_hash: {data_hash(project.records['D0001'][1])}" in text


def test_snapshot_is_opt_in(project_dir: Path) -> None:
    build()
    assert not (project_dir / "data.json").exists()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(snapshot="data.json"),
    )
    build()
    snapshot = json.loads((project_dir / "data.json").read_text("utf-8"))
    assert [r["id"] for r in snapshot["decisions"]["records"]] == ["D0001", "D0002"]


def test_outdated_lock_still_names_orphans(project_dir: Path) -> None:
    """After an `_api` bump the old lock is not trusted, but its paths are read."""
    build()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(short_title="Offline"),
    )
    lock_path = project_dir / "chancellor.lock"
    data = json.loads(lock_path.read_text("utf-8"))
    data["_api"]["version"] = "0"
    lock_path.write_text(json.dumps(data), "utf-8")
    result = build()
    old = "arch/decisions/D0002-render-documents-without-network-access.md"
    assert (old, "orphan") in result.statuses
    assert (project_dir / old).is_file()  # never deleted on an untrusted lock's word


def test_untracked_documents_warn_and_never_count_as_drift(
    project_dir: Path, cli
) -> None:
    """Files named like documents, known to no record or lock: warned, kept."""
    build()
    stray = project_dir / "arch" / "decisions" / "D0099-left-behind.md"
    stray.write_text("old\n", "utf-8")
    (project_dir / "arch" / "decisions" / "notes.md").write_text("mine\n", "utf-8")
    code, out, err = cli("build", "--check", "-q")
    assert code == 0 and "untracked\tarch/decisions/D0099-left-behind.md" in out
    assert "notes.md" not in out  # not named like a document of the kind
    assert (
        "warning: arch/decisions/D0099-left-behind.md is named like a document" in err
    )
    assert stray.is_file()
    code, _, err = cli("doctor")
    assert (
        code == ExitCode.CONFIG
        and "untracked: arch/decisions/D0099-left-behind.md" in err
    )
