"""Editable installs: code edits must reach the digests (0.1.0:D0017).

In a release, a code provider and the renderer are fingerprinted by their version string. An
editable install keeps its version across edits, so its source decides instead. It is no
degradation while that source can be hashed completely.
"""

from pathlib import Path

import pytest

from chancellor import codeload, hashing, providers
from chancellor.build import explain, run
from chancellor.project import Project
from chancellor.providers import builtin_providers


def test_source_digest_follows_content(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    module = tmp_path / "pkg" / "mod.py"
    module.write_text("X = 1\n", "utf-8")
    (tmp_path / "pkg" / "__pycache__").mkdir()
    (tmp_path / "pkg" / "__pycache__" / "mod.cpython-311.pyc").write_bytes(b"ignored")
    first = codeload.source_digest(tmp_path)
    assert codeload.source_digest(tmp_path) == first  # memoized within a load
    module.write_text("X = 2\n", "utf-8")
    codeload.reset_source_digests()
    assert codeload.source_digest(tmp_path) != first
    (tmp_path / "pkg" / "__pycache__" / "mod.cpython-311.pyc").write_bytes(
        b"still ignored"
    )
    codeload.reset_source_digests()
    second = codeload.source_digest(tmp_path)
    codeload.reset_source_digests()
    assert codeload.source_digest(tmp_path) == second


def test_editable_code_provider_is_fingerprinted_by_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builtin = builtin_providers()[1]
    monkeypatch.setattr(providers, "distribution_info", lambda name: ("0.1.0", True))
    monkeypatch.setattr(providers, "source_digest", lambda root: "c1:sha256:aaa")
    assert builtin.fingerprint({}) == "0.1.0 source c1:sha256:aaa"
    monkeypatch.setattr(providers, "distribution_info", lambda name: ("0.1.0", False))
    assert builtin.fingerprint({}) == "0.1.0"


@pytest.mark.usefixtures("project_dir")
def test_code_edit_in_editable_install_shows_as_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(providers, "distribution_info", lambda name: ("0.1.0", True))
    source = {"digest": "c1:sha256:before"}
    monkeypatch.setattr(providers, "source_digest", lambda root: source["digest"])
    monkeypatch.setattr(hashing, "source_digest", lambda root: source["digest"])
    run(Project.load())
    assert not run(Project.load(), check=True).drift
    source["digest"] = (
        "c1:sha256:after"  # a renderer or template edit in the working tree
    )
    assert run(Project.load(), check=True).drift
    message = "\n".join(explain(Project.load(), "D0001"))
    assert "api: the data format or the renderer changed" in message
    assert "provider builtin.jkrenzer 0.1.0 source c1:sha256:before" in message


@pytest.mark.usefixtures("project_dir", "released")
def test_release_install_is_fingerprinted_by_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert Project.load().registry.fingerprints()["builtin.jkrenzer"] == "0.1.0"
    released = hashing.renderer_fingerprint()
    monkeypatch.setattr(providers, "distribution_info", lambda name: ("0.1.0", True))
    assert hashing.renderer_fingerprint() != released  # editable: the source joins


@pytest.mark.usefixtures("released")
def test_renderer_fingerprint_covers_python_and_output_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same digest, same bytes; whatever shapes the output is in the api part."""
    base = hashing.renderer_fingerprint()
    deps = hashing.output_dependencies()
    assert {
        "jinja2",
        "mdformat",
        "mdformat-gfm",
        "ruamel-yaml",
        "pydantic",
        "rfc8785",
    } <= set(deps)
    bumped = {**deps, "mdformat": "9.9.9"}
    monkeypatch.setattr(hashing, "output_dependencies", lambda: bumped)
    assert hashing.renderer_fingerprint() != base
    monkeypatch.setattr(hashing, "output_dependencies", lambda: deps)
    monkeypatch.setattr(hashing.platform, "python_implementation", lambda: "PyPy")
    assert hashing.renderer_fingerprint() != base


@pytest.mark.usefixtures("project_dir")
def test_dependency_upgrade_shows_as_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    run(Project.load())
    deps = {**hashing.output_dependencies(), "jinja2": "99.0"}
    monkeypatch.setattr(hashing, "output_dependencies", lambda: deps)
    assert run(Project.load(), check=True).drift
    assert "api: the data format or the renderer changed" in "\n".join(
        explain(Project.load(), "D0001")
    )
