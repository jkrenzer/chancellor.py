"""Record-set versions, version schemes and absolute IDs (0.1.0:D0036, 0.1.0:D0029)."""

import json
import textwrap
from pathlib import Path

import pytest

from chancellor.build import explain, plan, render, run
from chancellor.config import config_model
from chancellor.errors import ConfigError, ExitCode, InputError
from chancellor.keys import ModuleKeys
from chancellor.project import Project
from chancellor.versions import (
    FreeScheme,
    Pep440Scheme,
    SemverScheme,
    absolute_id,
    semver_key,
    split_absolute,
)

from .conftest import edit, record
from .test_depends import interface, manifest
from .test_providers import add_provider

SEMVER, FREE = SemverScheme(), FreeScheme()


def versioned(
    project_dir: Path, version: str | None = "0.1.0", scheme: str = "semver"
) -> None:
    def change(data: dict) -> None:
        if version is not None:
            data["meta"] = {"chancellor": {"version": version}}
        data["config"]["chancellor"]["versioning"] = {"scheme": scheme}

    edit(project_dir / "chancellor.yaml", change)


def address(project_dir: Path, value: str) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0001").update(addresses=[value]),
    )


def test_semver_precedence_and_parsing() -> None:
    order = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "1.0.1",
        "1.10.0",
    ]
    assert sorted(order, key=semver_key) == order
    assert SEMVER.compare("1.0.0+build.5", "1.0.0") == 0
    for bad in ["1.0", "01.0.0", "1.0.0-", "v1.0.0", ""]:
        assert not SEMVER.is_version(bad)


def test_pep440_ordering() -> None:
    order = ["1.0.dev1", "1.0a1", "1.0b2", "1.0rc1", "1.0", "1.0.post1"]
    scheme = Pep440Scheme()
    assert sorted(order, key=scheme.key) == order
    assert not scheme.is_version("not a version")


def test_absolute_id_forms() -> None:
    assert absolute_id("0.1.0", "D0017", "{version}:{id}") == "0.1.0:D0017"
    assert absolute_id(None, "D0017", "{version}:{id}") is None
    assert split_absolute("0.1.0:D0017", "{version}:{id}", SEMVER) == ("0.1.0", "D0017")
    assert split_absolute("other:1.0.0:D0001", "{version}:{id}", SEMVER) is None
    assert split_absolute("other:1.0.0:D0001", "{version}:{id}", FREE) is None
    assert split_absolute("x:D0001", "{version}:{id}", FREE) == ("x", "D0001")
    assert split_absolute("https://example.org/D1", "{version}:{id}", FREE) is None
    assert split_absolute("D0017@0.1.0", "{id}@{version}", SEMVER) == ("0.1.0", "D0017")


@pytest.mark.parametrize(
    ("versioning", "message"),
    [
        ({"absolute_id": "{version}"}, "must contain the field {id}"),
        ({"absolute_id": "{v}:{id}"}, "unknown field v"),
        (
            {"scheme": "calver"},
            "Unknown version scheme type calver; available: builtin.free",
        ),
    ],
)
def test_bad_versioning_config_exits_1(
    project_dir: Path, versioning: dict, message: str
) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(versioning=versioning),
    )
    with pytest.raises(ConfigError, match=message):
        Project.load()


def test_free_scheme_checks_nothing(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0001")["revisions"].__setitem__(
            1, {"version": "first", "date": "2026-10-05", "description": "x"}
        ),
    )
    versioned(project_dir, version="anything", scheme="free")
    assert Project.load().record_set_version == "anything"


def test_semver_validates_versions_and_order(project_dir: Path) -> None:
    versioned(project_dir, version="0.1")
    with pytest.raises(
        InputError, match=r"meta\.chancellor\.version: '0\.1' is not a valid semver"
    ):
        Project.load()
    versioned(project_dir)

    def revisions(data: dict) -> list:
        return record(data, "decisions", "D0001")["revisions"]

    edit(
        project_dir / "chancellor.yaml", lambda d: revisions(d)[1].update(version="1.1")
    )
    with pytest.raises(
        InputError, match=r"revisions\[1\]\.version: '1\.1' is not a valid semver"
    ):
        Project.load()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: revisions(d)[1].update(version="0.9.0"),
    )
    with pytest.raises(
        InputError, match=r"revisions\[1\]\.version: '0\.9\.0' does not increase"
    ):
        Project.load()


def test_templates_see_version_and_absolute_ids(project_dir: Path) -> None:
    template = (
        "{{ absolute_id }} {{ meta.version }}\n"
        "{% for p in refs.partners %}{{ p.absolute_id }}\n{% endfor %}"
    )
    add_provider(
        project_dir, manifest("name"), template, interfaces=interface(["D0001"])
    )
    versioned(project_dir)
    project = Project.load()
    built = plan(project)
    text = render(project, next(d for d in built.documents if d.id == "I0001"), built)
    # The formatter joins the lines into one paragraph; the values are what matters.
    assert text.split() == ["0.1.0:I0001", "0.1.0", "0.1.0:D0001"]


def test_version_bump_rebuilds_everything(project_dir: Path) -> None:
    versioned(project_dir)
    run(Project.load())
    versioned(project_dir, version="0.2.0")
    assert (
        "meta: the record-set version or the absolute-ID format changed"
        in "\n".join(explain(Project.load(), "D0002"))
    )  # D0002 shows no version: still rebuilt
    assert run(Project.load(), check=True).drift


def test_current_absolute_reference_resolves_like_a_bare_one(project_dir: Path) -> None:
    versioned(project_dir)
    address(project_dir, "0.1.0:R0001")
    project = Project.load()
    assert project.resolved_refs(project.records["D0001"][1]) == ["R0001"]
    assert not project.historic_refs
    address(project_dir, "0.1.0:R0009")
    with pytest.raises(InputError, match="reference 0.1.0:R0009 names no record"):
        Project.load()


def test_historic_reference_warns_and_is_listed(project_dir: Path, cli) -> None:
    versioned(project_dir, version="0.2.0")
    address(project_dir, "0.1.0:R0001")
    # R0001 no longer lists D0001: a historic reference is no current link (doctor would
    # report the link as one-sided otherwise).
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "requirements", "R0001").update(addressed_by=["S0001"]),
    )
    code, _, err = cli("build", "--strict")
    assert code == 0  # not a degradation
    assert "historic reference 0.1.0:R0001 in decisions.D0001" in err
    code, out, _ = cli("doctor")
    assert (
        code == 0 and "historic reference: decisions.D0001 refers to 0.1.0:R0001" in out
    )


def test_newer_version_reference_is_invalid(cli, project_dir: Path) -> None:
    versioned(project_dir)
    address(project_dir, "0.2.0:R0001")
    code, _, err = cli("build")
    assert code == ExitCode.INPUT and "newer than the data (0.1.0)" in err


def test_bump_turns_current_references_historic(project_dir: Path) -> None:
    versioned(project_dir)
    address(project_dir, "0.1.0:R0001")
    assert not Project.load().historic_refs
    versioned(project_dir, version="0.2.0")
    assert Project.load().historic_refs == [("decisions", "D0001", "0.1.0:R0001")]


def test_templates_can_mark_historic_references(project_dir: Path) -> None:
    template = (
        "{% for p in refs.partners %}"
        "{{ p.historic }} {{ p.version }} {{ p.current.path if p.current else '-' }}\n"
        "{% endfor %}"
    )
    add_provider(
        project_dir,
        manifest("id"),
        template,
        interfaces=interface(["0.1.0:D0001", "0.1.0:D0099", "D0002"]),
    )
    versioned(project_dir, version="0.2.0")
    project = Project.load()
    built = plan(project)
    text = render(project, next(d for d in built.documents if d.id == "I0001"), built)
    assert text.split() == [
        "True",
        "0.1.0",
        "arch/decisions/D0001-yaml-storage.md",
        "True",
        "0.1.0",
        "-",
        "False",
        "0.2.0",
        "-",
    ]


def test_external_references_pass(project_dir: Path) -> None:
    versioned(project_dir)
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(
            addresses=["other-project:1.0.0:D0001", "https://example.org/spec"]
        ),
    )
    project = Project.load()
    assert not project.historic_refs


def test_command_arguments_take_absolute_ids(cli, project_dir: Path) -> None:
    versioned(project_dir, version="0.2.0")
    cli("build")
    code, out, _ = cli("hash", "0.2.0:D0001")
    assert code == 0 and out.startswith("D0001\tc1:sha256:")
    code, out, err = cli("explain", "0.1.0:D0001")
    assert (
        code == 0
        and "historic reference to 0.1.0:D0001; showing the current D0001" in err
    )
    assert cli("explain", "0.1.0:D0099")[0] == ExitCode.INPUT
    assert cli("hash", "0.3.0:D0001")[0] == ExitCode.INPUT


def test_doctor_notes_missing_version(cli, project_dir: Path) -> None:
    versioned(project_dir, version=None)
    code, out, _ = cli("doctor")
    assert code == 0 and "meta.chancellor.version is not set" in out


@pytest.mark.usefixtures("project_dir")
def test_meta_in_schemas(cli) -> None:
    code, out, _ = cli("schema", "data")
    assert code == 0 and "meta" in json.loads(out)["properties"]
    schema = config_model(Project.load().registry).model_json_schema()
    assert "versioning" in schema["properties"]


def test_meta_is_data(project_dir: Path) -> None:
    """`meta` holds data: defined twice across files, or malformed, is invalid input."""
    versioned(project_dir)
    (project_dir / "more.yaml").write_text(
        'meta:\n  chancellor:\n    version: "0.2.0"\n', "utf-8"
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["more.yaml"]),
    )
    with pytest.raises(InputError, match=r"meta\.chancellor\.version is defined in"):
        Project.load()
    edit(
        project_dir / "chancellor.yaml",
        lambda d: (
            d["config"]["chancellor"].pop("include"),
            d["meta"]["chancellor"].update(version=3),
        ),
    )
    with pytest.raises(InputError, match="meta.chancellor"):
        Project.load()


def test_meta_key_follows_module_keys(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d.update(meta={"records": {"version": "1.2.3"}}),
    )
    assert (
        Project.load(keys=ModuleKeys(overrides={"meta": "records"})).record_set_version
        == "1.2.3"
    )


def test_meta_and_absolute_id_are_reserved_names(project_dir: Path) -> None:
    title = "      title: {type: text}\n"
    bad = manifest("id").replace(
        title, title + "      absolute_id: {type: str, required: false}\n"
    )
    add_provider(project_dir, bad, "x\n", interfaces=[])
    with pytest.raises(
        ConfigError, match="field absolute_id is reserved in the template context"
    ):
        Project.load()


CALVER = '''
import re

from chancellor.api import VersionScheme


class CalVer(VersionScheme):
    """YYYY.MM versions."""

    def key(self, text):
        match = re.fullmatch(r"(\\d{4})\\.(\\d{2})", text)
        return (int(match.group(1)), int(match.group(2))) if match else None
'''


def test_provider_contributes_a_version_scheme(project_dir: Path) -> None:
    head = "_api:\n  version: 1.0.0\n  kind: chancellor_provider\nname: extprov\nversion: 1\n"
    folder = add_provider(
        project_dir,
        head + "version_schemes:\n  calver: schemes:CalVer\n",
        interfaces=[],
    )
    (folder / "schemes.py").write_text(textwrap.dedent(CALVER), "utf-8")
    edit(project_dir / "chancellor.yaml", lambda d: d.pop("interface"))
    edit(
        project_dir / "chancellor.yaml",
        lambda d: [
            rev.update(version=f"2026.{i + 1:02d}")
            for r in d["decisions"]["records"]
            + d["requirements"]["records"]
            + d["specifications"]["records"]
            + [
                d["decisions"]["core"],
                d["requirements"]["core"],
                d["specifications"]["core"],
            ]
            for i, rev in enumerate(r["revisions"])
        ],
    )
    versioned(project_dir, version="2026.10", scheme="extprov.calver")
    project = Project.load()
    assert type(project.version_scheme).__name__ == "CalVer"
    versioned(project_dir, version="2026.1", scheme="extprov.calver")
    with pytest.raises(InputError, match="not a valid extprov.calver version"):
        Project.load()


def test_import_path_scheme_is_fingerprinted(project_dir: Path) -> None:
    path = project_dir / "tools" / "calver.py"
    path.parent.mkdir()
    path.write_text(textwrap.dedent(CALVER), "utf-8")
    versioned(project_dir, version=None, scheme="tools/calver.py:CalVer")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: [
            rev.update(version=f"2026.{i + 1:02d}")
            for r in d["decisions"]["records"]
            + d["requirements"]["records"]
            + d["specifications"]["records"]
            + [
                d["decisions"]["core"],
                d["requirements"]["core"],
                d["specifications"]["core"],
            ]
            for i, rev in enumerate(r["revisions"])
        ],
    )
    project = Project.load()
    assert "code:tools/calver.py:CalVer" in project.code_fingerprints
    path.write_text("# not a scheme\nCalVer = 1\n", "utf-8")
    with pytest.raises(ConfigError, match="is not a VersionScheme subclass"):
        Project.load()
