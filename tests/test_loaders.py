"""Config loaders through the registry, and `--set` (0.1.0:D0034)."""

import json
import textwrap
from pathlib import Path

import pytest

from chancellor.errors import ConfigError, ExitCode
from chancellor.project import Project

from .conftest import edit
from .test_providers import add_provider

LOADER = """
from chancellor.api import ConfigLoader, LoadedConfig


class Fixed(ConfigLoader):
    def load(self):
        return LoadedConfig(data={"wrap_width": self.arguments.get("width", 60)}, origin="fixed")


class Broken(ConfigLoader):
    def load(self):
        raise RuntimeError("cannot reach the config store")


class NotALoader:
    pass
"""


def loaders(project_dir: Path, entries: list) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(loaders=entries),
    )


def with_tool(project_dir: Path) -> None:
    path = project_dir / "tools" / "loader.py"
    path.parent.mkdir(exist_ok=True)
    path.write_text(textwrap.dedent(LOADER), "utf-8")


def test_default_loader_is_resolved_through_the_registry(project_dir: Path) -> None:
    loaders(project_dir, ["builtin.data_file"])
    assert Project.load().config.wrap_width == 100


def test_provider_loader_priority_follows_declared_order(project_dir: Path) -> None:
    head = "_api:\n  version: 1.0.0\n  kind: chancellor_provider\nname: extprov\nversion: 1\n"
    folder = add_provider(
        project_dir, head + "config_loaders:\n  fixed: models:Fixed\n", interfaces=[]
    )
    (folder / "models.py").write_text(textwrap.dedent(LOADER), "utf-8")
    edit(project_dir / "chancellor.yaml", lambda d: d.pop("interface"))
    loaders(project_dir, ["extprov.fixed", "builtin.data_file"])
    assert Project.load().config.wrap_width == 60  # the provider's loader comes first
    loaders(project_dir, ["builtin.data_file", "extprov.fixed"])
    assert Project.load().config.wrap_width == 100  # the data file comes first


def test_import_path_loader_with_arguments(project_dir: Path) -> None:
    with_tool(project_dir)
    loaders(
        project_dir,
        [{"type": "tools/loader.py:Fixed", "width": 72}, "builtin.data_file"],
    )
    assert Project.load().config.wrap_width == 72


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        (
            "tools/loader.py:NotALoader",
            "loaders[0]: tools/loader.py:NotALoader is not a ConfigLoader",
        ),
        (
            "tools/loader.py:Broken",
            "loaders[0]: loader tools/loader.py:Broken failed: cannot reach",
        ),
        ("builtin.nope", "Unknown config loader type builtin.nope"),
        ({"width": 1}, "loaders[0]: name a loader type"),
    ],
)
def test_bad_loader_is_a_config_error(project_dir: Path, entry, message: str) -> None:
    with_tool(project_dir)
    loaders(project_dir, [entry])
    with pytest.raises(
        ConfigError, match=message.replace("[", r"\[").replace("]", r"\]")
    ):
        Project.load()


@pytest.mark.usefixtures("project_dir")
def test_set_has_the_highest_priority(cli, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHANCELLOR_WRAP_WIDTH", "70")
    assert Project.load(overrides={"wrap_width": 80}).config.wrap_width == 80
    code, out, _ = cli("--set", "wrap_width=80", "schema", "config")
    assert code == 0 and json.loads(out)


@pytest.mark.parametrize(
    ("pair", "message"),
    [
        ("wrap_width", "write it as KEY=VALUE"),
        ("include=[x]", "are read before any source"),
        ("wrap_width=!!int 80", "YAML tags are not allowed"),
        ("formatter=&a {type: builtin.none}", "YAML anchors are not allowed"),
    ],
)
@pytest.mark.usefixtures("project_dir")
def test_bad_set_exits_1(cli, pair: str, message: str) -> None:
    code, _, err = cli("--set", pair, "build")
    assert code == ExitCode.CONFIG and message in err


def test_set_is_logged_recorded_and_explained(cli, project_dir: Path) -> None:
    """Logged at INFO, recorded in the lock, named by `explain`."""
    code, _, err = cli("--set", "wrap_width=80", "build")
    assert code == 0 and "CLI override wrap_width = 80" in err
    lock = json.loads((project_dir / "chancellor.lock").read_text("utf-8"))
    assert lock["cli_overrides"] == {"wrap_width": 80}
    assert cli("build", "--check")[0] == ExitCode.DRIFT
    code, out, _ = cli("explain", "D0001")
    assert (
        "config: config/chancellor changed: CLI override wrap_width=80 in the lock, none now"
        in out
    )


def test_loaders_are_layout_and_main_file_only(project_dir: Path) -> None:
    digest = Project.load().config_digest
    loaders(project_dir, ["builtin.data_file"])
    assert Project.load().config_digest == digest
    (project_dir / "more.yaml").write_text(
        "config:\n  chancellor:\n    loaders: [builtin.data_file]\n", "utf-8"
    )
    edit(
        project_dir / "chancellor.yaml",
        lambda d: (
            d["config"]["chancellor"].pop("loaders"),
            d["config"]["chancellor"].update(include=["more.yaml"]),
        ),
    )
    with pytest.raises(ConfigError, match="must be set in the main data file"):
        Project.load()
