"""The command line and its exit codes (0.1.0:D0010)."""

import json
from pathlib import Path

import pytest

from chancellor import cli as cli_module
from chancellor import providers
from chancellor.builtin.jkrenzer import models
from chancellor.codeload import SourceDigest
from chancellor.errors import EXIT_CODE_MEANINGS, ExitCode
from chancellor.yamlio import dump

from .conftest import edit, record
from .test_models import INPUTS
from .test_providers import add_provider


def test_help_lists_the_exit_codes(cli) -> None:
    code, out, _ = cli("--help")
    assert code == 0
    for exit_code in ExitCode:
        assert f"{exit_code.value}  {EXIT_CODE_MEANINGS[exit_code]}" in out
    assert out.count("Result codes") == 0
    code, out, _ = cli("build", "--help")
    assert code == 0 and "3 drift" in out


def test_version(cli) -> None:
    assert cli("--version")[0] == 0


def test_usage_error_is_a_config_error(cli) -> None:
    assert cli("build", "--no-such-option")[0] == ExitCode.CONFIG


def test_no_data_file_is_a_config_error(
    cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    code, _, err = cli("build")
    assert code == ExitCode.CONFIG and "No chancellor.yaml" in err


def test_build_check_strict_codes(cli, project_dir: Path) -> None:
    code, out, _ = cli("build")
    assert code == 0 and "new\tarch/decisions/D0001-yaml-storage.md" in out
    assert "updated\tchancellor.lock" in out
    assert cli("build", "--check")[0] == 0
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(state="x"),
    )
    code, out, _ = cli("build", "--check", "-q")
    assert code == ExitCode.DRIFT and out.startswith("changed\t")
    # this editable checkout is hashed completely, so --strict passes ...
    assert cli("build", "--strict")[0] == 0


def test_strict_fails_when_the_editable_source_is_incomplete(
    cli, project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """... and fails once something in the source cannot be hashed (0.1.0:D0017)."""
    del project_dir
    incomplete = SourceDigest("c1:sha256:x", False, "compiled extension fast.so")
    monkeypatch.setattr(providers, "tree_digest", lambda root: incomplete)
    code, _, err = cli("build", "--strict")
    assert code == ExitCode.DEGRADED and "editable-install" in err
    assert "compiled extension fast.so" in err


@pytest.mark.usefixtures("project_dir")
@pytest.mark.usefixtures("released")
def test_strict_passes_without_degradations(cli) -> None:
    assert cli("build", "--strict")[0] == 0


def test_invalid_input_exits_2(cli, project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").pop("author"),
    )
    code, _, err = cli("build")
    assert code == ExitCode.INPUT and "author: Field required" in err


@pytest.mark.usefixtures("project_dir")
def test_lint_without_linter_exits_1(cli) -> None:
    code, _, err = cli("lint")
    assert code == ExitCode.CONFIG and "No linter set" in err


def test_lint_problems_exit_5(cli, project_dir: Path) -> None:
    head = "_api:\n  version: 1.0.0\n  kind: chancellor_provider\nname: extprov\nversion: 1\n"
    folder = add_provider(
        project_dir, head + "linters:\n  strict: models:FailingLinter\n", interfaces=[]
    )
    (folder / "models.py").write_text(
        "from chancellor.api import LintResult, Linter\n\n"
        "class FailingLinter(Linter):\n"
        "    def lint(self, paths, context):\n"
        "        return LintResult(problems=True, output='finding', returncode=1)\n",
        "utf-8",
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: (
            d.pop("interface"),
            d["config"]["chancellor"].update(linter={"type": "extprov.strict"}),
        ),
    )
    code, out, _ = cli("lint")
    assert code == ExitCode.LINT and "finding" in out


def test_unknown_linter_type_lists_available(cli, project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(linter={"type": "builtin.shell"}),
    )
    code, _, err = cli("lint")
    assert code == ExitCode.CONFIG and "available: builtin.none" in err


@pytest.mark.usefixtures("project_dir")
def test_internal_error_exits_6(cli, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_build", boom)
    code, _, err = cli("build")
    assert code == ExitCode.INTERNAL and "RuntimeError: boom" in err


def test_render_from_stdin_without_project(
    cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    code, out, _ = cli("render", "adr", "-", stdin=dump(INPUTS[models.Decision]))
    assert code == 0
    assert out.startswith("---\ntitle: Full Title\nid: D0001\n")
    assert "## Alternatives Considered" in out and "No alternative evaluation" in out


def test_render_invalid_input_exits_2(
    cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    code, _, err = cli("render", "adr", "-", stdin="title: x\n")
    assert code == ExitCode.INPUT and "Invalid Decision input" in err


@pytest.mark.usefixtures("project_dir")
def test_render_unknown_kind_exits_1(cli) -> None:
    code, _, err = cli("render", "nope", "-", stdin="{}")
    assert code == ExitCode.CONFIG and "known: decisions, adr, adr-core" in err


def test_render_core_takes_the_projects_index(cli, project_dir: Path) -> None:
    source = project_dir / "core.yaml"
    source.write_text(dump(INPUTS[models.DecisionCore]), "utf-8")
    code, out, _ = cli("render", "adr-core", str(source))
    assert code == 0 and "[D0001: YAML Storage](D0001-yaml-storage.md)" in out


@pytest.mark.usefixtures("project_dir")
@pytest.mark.parametrize(
    "name", ["config", "data", "provider", "lock", "adr", "requirements", "asr-core"]
)
def test_schema(cli, name: str) -> None:
    code, out, _ = cli("schema", name)
    assert code == 0 and isinstance(json.loads(out), dict)


@pytest.mark.usefixtures("project_dir")
def test_hash(cli) -> None:
    code, out, _ = cli("hash", "D0001")
    assert code == 0 and out.startswith("D0001\tc1:sha256:")
    assert cli("hash", "D9999")[0] == ExitCode.CONFIG
    assert len(cli("hash")[1].splitlines()) == 7


def test_providers_lists_the_resolved_set(cli, project_dir: Path) -> None:
    code, out, _ = cli("providers")
    lines = out.splitlines()
    assert code == 0 and [line.split("\t")[0] for line in lines] == [
        "builtin",
        "builtin.jkrenzer",
    ]
    assert lines[1].endswith("decisions, requirements, specifications")
    add_provider(project_dir)
    assert (
        cli("providers")[1]
        .splitlines()[-1]
        .startswith("extprov\tarch/providers/extprov\tdeclarative\tc1:sha256:")
    )


def test_explain(cli, project_dir: Path) -> None:
    cli("build")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "decisions", "D0002").update(state="x"),
    )
    code, out, _ = cli("explain", "D0002")
    assert code == 0 and "data: the record's own data changed" in out
    assert cli("explain", "D9999")[0] == ExitCode.CONFIG


def test_doctor(cli, project_dir: Path) -> None:
    (project_dir / "pyproject.toml").write_text(
        "[tool.pymarkdown]\nplugins.md013.line_length = 80\n", "utf-8"
    )
    code, _, err = cli("doctor")
    assert code == ExitCode.CONFIG and "plugins.md013.line_length is 80" in err
    (project_dir / "pyproject.toml").write_text(
        "[tool.pymarkdown]\nplugins.md013.line_length = 100\n", "utf-8"
    )
    edit(project_dir / "chancellor.yaml", lambda d: d.update(tasks=[{"id": "T1"}]))
    code, out, _ = cli("doctor")
    assert code == 0 and "section tasks belongs to no registered kind" in out


def test_doctor_reports_missing_provider(cli, project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            providers=[{"name": "ghost", "path": "ghost"}]
        ),
    )
    code, _, err = cli("doctor")
    assert code == ExitCode.CONFIG and "provider ghost is declared in config" in err


def test_doctor_reports_one_sided_links(cli, project_dir: Path) -> None:
    """`addresses` and `addressed_by` must list each other (declared by inverse_refs)."""
    edit(
        project_dir / "chancellor.yaml",
        lambda d: record(d, "requirements", "R0001").update(addressed_by=["S0001"]),
    )
    code, _, err = cli("doctor")
    assert code == ExitCode.INPUT
    assert (
        "one-sided link: decisions.D0001.addresses lists R0001, but R0001.addressed_by does "
        "not list D0001"
    ) in err


@pytest.mark.usefixtures("project_dir")
def test_doctor_notes_unreferenced_records(cli) -> None:
    code, out, _ = cli("doctor")
    assert code == 0
    assert "unreferenced: decisions.D0002 is referenced by no record" in out
    assert (
        "unreferenced: decisions.D0000" not in out
    )  # core documents are not expected refs
    assert "unreferenced: requirements.R0001" not in out


FORMATTER = """
from chancellor.api import Formatter, Linter, LintResult


class Upper(Formatter):
    def format(self, text, context):
        return text.upper()


class Strict(Linter):
    def lint(self, paths, context):
        return LintResult(problems=True, output="from file")
"""


def test_formatter_and_linter_by_import_path(cli, project_dir: Path) -> None:
    """Types named as path/to/file.py:Class; code edits reach the digest."""
    module = project_dir / "tools" / "fmt.py"
    module.parent.mkdir()
    module.write_text(FORMATTER, "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            formatter={"type": "tools/fmt.py:Upper"},
            linter={"type": "tools/fmt.py:Strict"},
        ),
    )
    assert cli("build")[0] == 0
    text = (project_dir / "arch/decisions/D0001-yaml-storage.md").read_text("utf-8")
    assert "## CONTEXT" in text
    code, out, _ = cli("lint")
    assert code == ExitCode.LINT and "from file" in out
    module.write_text(FORMATTER.replace("text.upper()", "text.lower()"), "utf-8")
    code, out, _ = cli("explain", "D0001")
    assert "providers: code tools/fmt.py:Upper" in out
    assert cli("build", "--check")[0] == ExitCode.DRIFT


def test_import_path_type_must_subclass(cli, project_dir: Path) -> None:
    module = project_dir / "tools" / "fmt.py"
    module.parent.mkdir()
    module.write_text(FORMATTER, "utf-8")
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            formatter={"type": "tools/fmt.py:Strict"}
        ),
    )
    code, _, err = cli("build")
    assert code == ExitCode.CONFIG
    assert (
        "config.chancellor.formatter.type: tools/fmt.py:Strict is not a Formatter subclass"
        in err
    )


def test_record_data_twice_exits_2_config_twice_exits_1(cli, project_dir: Path) -> None:
    """Each case asserted through the CLI."""
    (project_dir / "more.yaml").write_text(
        "decisions:\n  core:\n    title: Other\n", "utf-8"
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(include=["more.yaml"]),
    )
    assert cli("build")[0] == ExitCode.INPUT
    assert cli("doctor")[0] == ExitCode.INPUT
    (project_dir / "more.yaml").write_text(
        "config:\n  chancellor:\n    wrap_width: 80\n", "utf-8"
    )
    assert cli("build")[0] == ExitCode.CONFIG
