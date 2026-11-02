"""One fingerprinting path for every code reference (0.1.0:D0031).

Modules for these tests live in a temporary folder put on `sys.path`, so they are loose code
that no distribution owns.
"""

import importlib
import os
import sys
import textwrap
from pathlib import Path

import pytest

from chancellor import codeload
from chancellor.build import explain, run
from chancellor.codeload import code_fingerprint
from chancellor.project import Project

from .conftest import edit
from .test_providers import add_provider


def write(folder: Path, relative: str, text: str) -> Path:
    path = folder / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), "utf-8")
    return path


def fingerprint(module_name: str):
    codeload.reset_source_digests()
    importlib.invalidate_caches()
    return code_fingerprint(importlib.import_module(module_name))


def test_imported_helper_and_package_init_enter_the_digest(code_dir: Path) -> None:
    write(code_dir, "g1a.py", "import g1pkg.helper\n")
    init = write(code_dir, "g1pkg/__init__.py", "")
    helper = write(code_dir, "g1pkg/helper.py", "X = 1\n")
    first = fingerprint("g1a")
    helper.write_text("X = 2\n", "utf-8")
    second = code_fingerprint(sys.modules["g1a"])
    assert second == first  # memoized within one load
    codeload.reset_source_digests()
    second = code_fingerprint(sys.modules["g1a"])
    assert second.value != first.value
    init.write_text("# runs on import\n", "utf-8")
    codeload.reset_source_digests()
    assert code_fingerprint(sys.modules["g1a"]).value != second.value
    assert not first.degradations


def test_resolution_does_not_execute_parent_packages(code_dir: Path) -> None:
    """Walking `g1side.sub` must not run `g1side/__init__.py`."""
    marker = code_dir / "executed"
    write(code_dir, "g1side/__init__.py", f"open({str(marker)!r}, 'w').close()\n")
    write(code_dir, "g1side/sub.py", "Y = 1\n")
    write(code_dir, "g1b.py", "def later():\n    import g1side.sub\n")
    result = fingerprint("g1b")
    assert not marker.exists()
    assert not result.degradations


def test_stdlib_distributions_and_chancellor_stop_the_walk(
    code_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write(
        code_dir, "g1c.py", "import json\nimport chancellor.api\nimport ruamel.yaml\n"
    )
    monkeypatch.setattr(codeload, "distribution_info", lambda name: ("1.2.3", False))
    released = fingerprint("g1c")
    assert not released.degradations
    monkeypatch.setattr(codeload, "distribution_info", lambda name: ("1.2.3", True))
    editable = fingerprint("g1c")
    assert editable.value != released.value  # the source digest joins the version
    assert not editable.degradations  # its tree is hashed completely
    monkeypatch.setattr(
        codeload,
        "tree_digest",
        lambda root: codeload.SourceDigest("c1:sha256:x", False, "x.so"),
    )
    incomplete = fingerprint("g1c")
    assert {(d.code, d.subject) for d in incomplete.degradations} == {
        ("editable-install", "ruamel.yaml")
    }


def test_unresolvable_and_computed_imports_degrade(code_dir: Path) -> None:
    write(code_dir, "g1d.py", "def f():\n    import g1_missing_module\n")
    write(
        code_dir,
        "g1e.py",
        "import importlib\n\ndef f(name):\n    return importlib.import_module(name)\n",
    )
    assert [d.code for d in fingerprint("g1d").degradations] == ["unfingerprinted-code"]
    assert "computed" in fingerprint("g1e").degradations[0].message


def test_guarded_optional_import_is_absent_not_degraded(code_dir: Path) -> None:
    """An optional dependency appearing later moves the digest."""
    write(
        code_dir,
        "g1f.py",
        "try:\n    import g1_optional\nexcept ImportError:\n    g1_optional = None\n",
    )
    absent = fingerprint("g1f")
    assert not absent.degradations
    write(code_dir, "g1_optional.py", "Z = 1\n")
    assert fingerprint("g1f").value != absent.value


def test_digest_does_not_depend_on_load_order(code_dir: Path) -> None:
    write(code_dir, "g1shared.py", "S = 1\n")
    write(code_dir, "g1g.py", "import g1shared\n")
    cold = fingerprint("g1g").value
    importlib.import_module("g1shared")
    assert fingerprint("g1g").value == cold


def test_review_repro_external_model_change_is_drift(
    code_dir: Path, project_dir: Path
) -> None:
    """A provider model from a module on sys.path: an edit to it must show as drift."""
    module = write(
        code_dir,
        "extmod.py",
        """
        from chancellor.api import Model

        class Task(Model):
            title: str
        """,
    )
    manifest = (
        "_api:\n  version: 1.0.0\n  kind: chancellor_provider\nname: extprov\nversion: 1\n"
        "kinds:\n  interface:\n    folder: arch/interface\n    templates:\n"
        "      records: extprov/interface.md.j2\n    model: extmod:Task\n"
        "templates:\n  directory: templates\n"
    )
    add_provider(
        project_dir,
        manifest,
        "{{ title }}\n",
        interfaces=[{"id": "T1", "title": "hello world"}],
    )
    run(Project.load())
    assert not run(Project.load(), check=True).drift
    module.write_text(
        module.read_text("utf-8") + textwrap.dedent("""
        def model_serialize(self):
            return {**Model.model_serialize(self), "title": self.title.upper()}

        Task.model_serialize = model_serialize
        """),
        "utf-8",
    )
    assert run(Project.load(), check=True).drift
    assert "providers: provider extprov" in "\n".join(explain(Project.load(), "T1"))


def test_file_override_helper_edit_rebuilds(code_dir: Path, project_dir: Path) -> None:
    helper = write(code_dir, "g1helpers.py", "PREFIX = 'CH'\n")
    path = project_dir / "arch" / "models" / "records.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "import g1helpers\nfrom tests.traced import TracedDecision\n", "utf-8"
    )

    def change(data: dict) -> None:
        data["config"]["chancellor"]["kinds"] = {
            "decisions": {"model": "arch/models/records.py:TracedDecision"}
        }
        for item in data["decisions"]["records"]:
            item["source"] = ["item-57"]

    edit(project_dir / "chancellor.yaml", change)
    run(Project.load())
    helper.write_text("PREFIX = 'XX'\n", "utf-8")
    message = "\n".join(explain(Project.load(), "D0001"))
    assert "model override of kind decisions" in message
    # every document rebuilds, and each names the override that moved.
    assert "model override of kind decisions" in "\n".join(
        explain(Project.load(), "R0001")
    )


def test_unversioned_provider_with_unsafe_code_stays_degraded(
    code_dir: Path, project_dir: Path
) -> None:
    write(
        code_dir,
        "g1unsafe.py",
        """
        from chancellor.api import Model

        def load(name):
            import importlib
            return importlib.import_module(name)

        class Task(Model):
            title: str
        """,
    )
    manifest = (
        "_api:\n  version: 1.0.0\n  kind: chancellor_provider\nname: extprov\n"
        "kinds:\n  interface:\n    folder: arch/interface\n    templates:\n"
        "      records: extprov/interface.md.j2\n    model: g1unsafe:Task\n"
        "templates:\n  directory: templates\n"
    )
    add_provider(project_dir, manifest, "{{ title }}\n", interfaces=[])
    codes = {(d.code, d.subject) for d in Project.load().degradations}
    assert ("unversioned-provider", "extprov") in codes
    assert ("unfingerprinted-code", "g1unsafe") in codes


def test_file_module_runs_the_bytes_it_fingerprints(tmp_path: Path) -> None:
    """An edit of the same length within the timestamp resolution must not run stale bytecode."""
    path = tmp_path / "same.py"
    path.write_text("VALUE = 'aaa'\n", "utf-8")
    first, _ = codeload.load_file_module(path, "_chancellor_test.same")
    stat = path.stat()
    path.write_text("VALUE = 'bbb'\n", "utf-8")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))  # same size, same mtime
    second, _ = codeload.load_file_module(path, "_chancellor_test.same")
    assert (first.VALUE, second.VALUE) == ("aaa", "bbb")
