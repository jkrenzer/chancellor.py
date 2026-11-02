"""Rules about chancellor's own source that a code review would otherwise have to catch."""

import re
from pathlib import Path

SOURCE = Path(__file__).parent.parent / "src" / "chancellor"
FILES = sorted(SOURCE.rglob("*.py"))


def matches(pattern: str) -> list[str]:
    regex = re.compile(pattern)
    return [
        f"{path.relative_to(SOURCE)}:{number}"
        for path in FILES
        for number, line in enumerate(path.read_text("utf-8").splitlines(), 1)
        if regex.search(line)
    ]


def test_no_path_resolution_from_own_location() -> None:
    """The project root never depends on where chancellor is installed."""
    assert not matches(r"__file__")


def test_module_key_is_never_compared_as_a_literal() -> None:
    """Compare against ModuleKeys, never the default string."""
    assert not matches(r"""[=!]=\s*["']chancellor["']|["']chancellor["']\s*[=!]=""")


def test_pyyaml_is_never_imported() -> None:
    """Decision 4: YAML goes through ruamel.yaml only."""
    assert not matches(r"^\s*(import yaml\b|from yaml\b)")


def test_output_paths_are_built_in_one_place() -> None:
    """Invariant: output_path_for is the only constructor of output paths. A model may name
    its own file (an index links records by file name), but only paths.py joins a folder.
    """
    callers = {hit.split(":")[0] for hit in matches(r"\.output_name\(")}
    assert callers <= {"paths.py", "builtin/jkrenzer/models.py"}, callers
    assert {hit.split(":")[0] for hit in matches(r"output_path_for\(")} <= {
        "paths.py",
        "project.py",
    }


def test_only_write_module_writes_files() -> None:
    """Invariant: one write path; build outputs are written through write.apply only."""
    writers = matches(r"\.write_(bytes|text)\(|\.unlink\(")
    assert all(hit.startswith("write.py:") for hit in writers), writers
