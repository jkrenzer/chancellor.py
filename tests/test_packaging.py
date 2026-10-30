"""Packaging checks."""

import importlib.metadata
import importlib.resources

from typer.testing import CliRunner

import chancellor
from chancellor.cli import app


def test_package_imports() -> None:
    """The package imports in the configured src layout."""
    assert chancellor.__name__ == "chancellor"


def test_version_matches_metadata() -> None:
    assert chancellor.__version__ == importlib.metadata.version("chancellor")


def test_builtin_providers_are_packaged() -> None:
    for name in ("core", "jkrenzer"):
        provider = importlib.resources.files("chancellor") / "builtin" / name
        assert (provider / "chancellor-provider.yaml").is_file()
    templates = (
        importlib.resources.files("chancellor") / "builtin" / "jkrenzer" / "templates"
    )
    assert (templates / "decision.md.j2").is_file()


def test_cli_version_exits_successfully() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == chancellor.__version__
