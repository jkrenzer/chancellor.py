"""Shared fixtures: a copy of the sample project and a CLI runner returning exit codes."""

import io
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from chancellor import codeload, providers
from chancellor.cli import main
from chancellor.yamlio import dump, load

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "sample"
GOLDEN = Path(__file__).parent / "golden"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        help="Rewrite the golden files from the current rendering.",
    )


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("CHANCELLOR_"):
            monkeypatch.delenv(name)


@pytest.fixture
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The sample project in a temporary folder, which is the working directory."""
    shutil.copy(SAMPLE / "chancellor.yaml", tmp_path / "chancellor.yaml")
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def released(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend chancellor is a released, non-editable install: no degradations."""
    monkeypatch.setattr(providers, "distribution_info", lambda name: ("0.1.0", False))


def edit(path: Path, change: Callable[[dict[str, Any]], None]) -> None:
    """Load a YAML file, change the data in place, write it back."""
    data = load(path)
    change(data)
    path.write_text(dump(data), encoding="utf-8")


def record(data: dict[str, Any], kind: str, record_id: str) -> dict[str, Any]:
    """The raw record `record_id` of `kind` in a data tree."""
    return next(r for r in data[kind]["records"] if r["id"] == record_id)


@pytest.fixture
def cli(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    """Run the CLI in-process: returns (exit code, stdout, stderr)."""

    def run(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
        if stdin is not None:
            monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
        capsys.readouterr()
        code = main(list(args))
        out, err = capsys.readouterr()
        return code, out, err

    return run


@pytest.fixture
def code_dir(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """A folder on sys.path for loose test modules; their imports are forgotten afterwards."""
    folder = tmp_path_factory.mktemp("code")
    monkeypatch.syspath_prepend(str(folder))
    before = set(sys.modules)
    yield folder
    for name in set(sys.modules) - before:
        sys.modules.pop(name, None)
    codeload.reset_source_digests()
