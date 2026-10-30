"""Rendered documents: golden files, front matter, wrapping, lint cleanliness."""

import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from chancellor.build import run
from chancellor.builtin.jkrenzer.models import Decision
from chancellor.errors import ConfigError
from chancellor.hashing import data_hash
from chancellor.project import Project
from chancellor.yamlio import dump_front_matter, parse

from .conftest import GOLDEN, edit, record

GOLDEN_SAMPLE = GOLDEN / "sample"


def documents(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted((directory / "arch").rglob("*.md"))
    }


def test_golden(project_dir: Path, request: pytest.FixtureRequest) -> None:
    """The sample project renders to the committed golden files, byte for byte.

    Regenerate deliberately with `poe golden`, together with a version bump.
    """
    run(Project.load())
    rendered = documents(project_dir)
    if request.config.getoption("--update-golden"):
        shutil.rmtree(GOLDEN_SAMPLE, ignore_errors=True)
        for rel, content in rendered.items():
            target = GOLDEN_SAMPLE / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    assert rendered == documents(GOLDEN_SAMPLE)


def front(text: str) -> dict:
    header = text.split("---\n")[1]
    return parse(header, "front matter")


def test_front_matter_order_and_types(project_dir: Path) -> None:
    run(Project.load())
    text = (project_dir / "arch/decisions/D0001-yaml-storage.md").read_text("utf-8")
    data = front(text)
    # Front matter follows the model's declaration, with the link right after the ID and the
    # data hash last.
    assert list(data) == [*Decision.front_matter, "data_hash"]
    assert list(data)[:3] == ["title", "id", "addresses"]
    assert data["version"] == "1.1.0" and data["date"] == "2026-10-02"
    assert data["tags"] == ["storage", {"area": "data"}]
    assert text.startswith("---\n") and "\n---\n\n## Context\n" in text


def test_wrapping_follows_config_and_keeps_structure(project_dir: Path) -> None:
    long_url = "https://example.org/" + "x" * 120

    def change(data: dict) -> None:
        data["config"]["chancellor"]["wrap_width"] = 60
        record(data, "decisions", "D0002")["context"] = (
            "word " * 40
            + f"\n\nSee {long_url} for details.\n\n```text\n"
            + "code " * 30
            + "\n```\n"
        )
        record(data, "decisions", "D0002")["decision"] = [
            "First point.\n- nested point",
            "Second.",
        ]

    edit(project_dir / "chancellor.yaml", change)
    run(Project.load())
    body = (
        project_dir / "arch/decisions/D0002-render-documents-without-network-access.md"
    ).read_text("utf-8")
    body = body.split("\n---\n", 1)[1]
    in_code = False
    for line in body.splitlines():
        in_code = in_code != line.startswith("```")
        if not in_code and long_url not in line and not line.startswith("```"):
            assert len(line) <= 60, line
    assert long_url in body and "code " * 30 in body
    assert "- First point.\n  - nested point\n- Second." in body


def test_none_formatter_leaves_the_body(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(formatter={"type": "builtin.none"}),
    )
    run(Project.load())
    text = (project_dir / "arch/decisions/D0001-yaml-storage.md").read_text("utf-8")
    assert "that\ntools can validate" in text  # line breaks of the data, not wrapped


def test_formatter_arguments_are_validated(project_dir: Path) -> None:
    edit(
        project_dir / "chancellor.yaml",
        lambda d: d["config"]["chancellor"].update(
            formatter={"type": "builtin.mdformat", "wrap": 0}
        ),
    )
    with pytest.raises(ConfigError, match="formatter builtin.mdformat"):
        run(Project.load())


def test_golden_files_pass_pymarkdown() -> None:
    pymarkdown = pytest.importorskip("pymarkdown.api")
    config = Path(__file__).parent.parent / "pyproject.toml"
    api = pymarkdown.PyMarkdownApi().configuration_file_path(str(config))
    failures = []
    for path in sorted(GOLDEN_SAMPLE.rglob("*.md")):
        failures += [
            f"{path.name}: {f.rule_id} {f.line_number}"
            for f in api.scan_path(str(path)).scan_failures
        ]
    assert not failures


def test_block_scalar_items_keep_lists_tight(project_dir: Path) -> None:
    """A `- |` item keeps its trailing LF in the data (0.1.0:D0006), but must not loosen the
    rendered list when other items follow it."""

    def change(data: dict) -> None:
        item = record(data, "decisions", "D0002")
        item["decision"] = ["First line\nsecond line\n", "Next point.\n", "Last."]
        item["references"] = [
            {
                "designation": "Source",
                "description": "Block text.\n",
                "pointers": ["p\n"],
            },
            {"designation": "Other"},
        ]
        data["decisions"]["core"]["rule_sets"][0]["rules"] = [
            "Rule one\nwrapped.\n",
            "Rule two.",
        ]
        item["description"] = "Indexed description.\n"

    edit(project_dir / "chancellor.yaml", change)
    run(Project.load())
    folder = project_dir / "arch/decisions"
    body = (folder / "D0002-render-documents-without-network-access.md").read_text(
        "utf-8"
    )
    assert "- First line second line\n- Next point.\n- Last.\n" in body
    assert "- **Source**: Block text.\n  - p\n- **Other**.\n" in body
    core = (folder / "D0000-decision-core.md").read_text("utf-8")
    assert "- Rule one wrapped.\n- Rule two.\n" in core
    assert "Indexed description.\n  - Tags" not in core
    assert "):\n  Indexed description.\n\n" not in core.replace("- [D0001", "")


def test_front_matter_respects_wrap_width_without_changing_data(
    project_dir: Path,
) -> None:
    """Long front-matter values become block scalars within the width; they load back
    to the record's own data, so the data hash is unchanged."""
    run(Project.load())
    project = Project.load()
    record_model = project.records["D0002"][1]
    text = (
        project_dir / "arch/decisions/D0002-render-documents-without-network-access.md"
    ).read_text("utf-8")
    header = text.split("---\n")[1]
    assert "description: >-\n" in header
    assert all(len(line) <= 100 for line in header.splitlines())
    loaded = parse(header, "front matter")
    assert loaded["description"] == record_model.description
    assert (
        loaded["revisions"][0]["description"] == record_model.revisions[0].description
    )
    assert "    description: >-\n" in header
    assert loaded["data_hash"] == data_hash(record_model)


def test_front_matter_folding_round_trips() -> None:
    rng = random.Random(16)
    words = [
        "alpha",
        "beta:",
        "gamma",
        "#",
        "'q'",
        '"dq"',
        "x-y,",
        "[a]",
        "{b}",
        "\u00e4",
        "-",
    ]
    words += ["?", "!", "%", "@", "`t`", "1.0.0", "null"]

    def text() -> str:
        value = " ".join(rng.choice(words) for _ in range(rng.randint(1, 40)))
        variant = rng.random()
        if variant < 0.1:
            value = " " + value
        elif variant < 0.2:
            value = value.replace(" ", "\n", 2)
        elif variant < 0.25:
            value = value.replace(" ", "  ", 1)
        return value

    for _ in range(400):
        data = {
            "title": text(),
            "tags": [text(), {"area": text()}],
            "revisions": [{"version": "1.0.0", "description": text()}],
        }
        width = rng.choice([60, 80, 100])
        out = dump_front_matter(data, width)
        assert parse(out, "front matter") == data
        clean = all(
            v == v.strip() and "  " not in v and "\n" not in v for v in _strings(data)
        )
        if clean:
            assert all(len(line) <= width for line in out.splitlines()), out


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def test_golden_files_pass_the_repository_mdformat() -> None:
    """Mdformat with the repository's plugins keeps the folded front matter as written."""
    pytest.importorskip("mdformat_front_matters")
    files = [str(p) for p in sorted(GOLDEN_SAMPLE.rglob("*.md"))]
    result = subprocess.run(
        [sys.executable, "-m", "mdformat", "--check", *files],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
