"""YAML reading and writing, with ruamel.yaml only; PyYAML is never imported."""

from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString, LiteralScalarString

from .errors import ConfigError, InputError


def _safe(typ: str = "safe") -> YAML:
    yaml = YAML(typ=typ, pure=True)
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = 4096
    # Sequences indented under their key, as mdformat's front-matter plugins write them, so a
    # consumer formatting Markdown with those plugins does not rewrite chancellor's output.
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.sort_base_mapping_type_on_output = False  # type: ignore[assignment]
    return yaml


def parse(
    text: str, where: str, *, error: type[ConfigError | InputError] = InputError
) -> Any:
    """Parse YAML text; a syntax error names `where`."""
    try:
        return _safe().load(text)
    except YAMLError as exc:
        raise error(f"{where}: invalid YAML: {exc}") from exc


def parse_plain_value(text: str, where: str) -> Any:
    """A YAML scalar or collection as plain data: tags, anchors and aliases are refused, so
    nothing beyond strings, numbers, booleans, null, lists and mappings can arrive."""
    try:
        tokens = list(_safe().scan(text))
    except YAMLError as exc:
        raise ConfigError(f"{where}: invalid YAML value: {exc}") from exc
    refused = {"TagToken": "tags", "AnchorToken": "anchors", "AliasToken": "aliases"}
    for token in tokens:
        kind = type(token).__name__
        if kind in refused:
            raise ConfigError(
                f"{where}: YAML {refused[kind]} are not allowed in a value"
            )
    return parse(text, where, error=ConfigError)


def load(path: Path, *, error: type[ConfigError | InputError] = InputError) -> Any:
    """Parse a YAML file."""
    try:
        text = path.read_text("utf-8")
    except OSError as exc:
        raise error(f"{path}: {exc.strerror or exc}") from exc
    return parse(text, str(path), error=error)


def dump(data: Any) -> str:
    """Block-style YAML in the mapping's own key order, one value per line."""
    stream = StringIO()
    _safe().dump(data, stream)
    return stream.getvalue()


def dump_front_matter(data: dict[str, Any], width: int) -> str:
    """Front matter as YAML whose lines stay within `width` where the values allow it.

    A string that would overflow its line is written as a block scalar: a single-line value as
    a folded block (`>-`) broken at spaces, a multi-line value as a literal block. Both load
    back to the identical string, so data and digests are unaffected. mdformat's front-matter
    plugin keeps block scalars as written, and the lint sees lines within the width. A word
    longer than the width stays whole. Everything else is written as `dump` writes it.
    """
    stream = StringIO()
    _safe("rt").dump(_blocks(data, 0, width), stream)
    return stream.getvalue()


def _blocks(mapping: dict[str, Any], column: int, width: int) -> dict[str, Any]:
    """Copy of `mapping` (keys at `column`) with overflowing strings turned into blocks."""
    result: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, str):
            inline = " " * column + dump({key: value}).splitlines()[0]
            result[key] = (
                _block(value, column + 2, width)
                if len(inline) > width or "\n" in value
                else value
            )
        elif isinstance(value, dict):
            result[key] = _blocks(value, column + 2, width)
        elif isinstance(value, list):
            result[key] = _sequence_blocks(value, column + 2, width)
        else:
            result[key] = value
    return result


def _sequence_blocks(items: list[Any], dash: int, width: int) -> list[Any]:
    """Copy of a sequence whose dashes sit at `dash`; item content starts two columns later."""
    result: list[Any] = []
    for item in items:
        if isinstance(item, str):
            inline = " " * dash + dump([item]).splitlines()[0]
            result.append(
                _block(item, dash + 2, width)
                if len(inline) > width or "\n" in item
                else item
            )
        elif isinstance(item, dict):
            result.append(_blocks(item, dash + 2, width))
        elif isinstance(item, list):
            result.append(_sequence_blocks(item, dash + 2, width))
        else:
            result.append(item)
    return result


def _block(text: str, indent: int, width: int) -> str:
    """`text` as a block scalar indented by `indent`, or unchanged if no block keeps it exact."""
    if "\n" in text:
        lines = text.split("\n")
        exact = (
            text.strip() != ""
            and not text.startswith((" ", "\n"))
            and not any(line != line.rstrip() or "\t" in line for line in lines)
        )
        return LiteralScalarString(text) if exact else text
    if text != text.strip() or "  " in text or "\t" in text or not text:
        return text  # folding would not load back to the same string
    budget = max(width - indent, 1)
    positions: list[int] = []
    line_start = 0
    for index, char in enumerate(text):
        if char == " ":
            next_space = text.find(" ", index + 1)
            word_end = len(text) if next_space == -1 else next_space
            if word_end - line_start > budget:
                positions.append(index)
                line_start = index + 1
    # Called only when the inline form overflows, so a block helps even when the text fits on
    # one block line: the key and any quoting move off that line.
    folded = FoldedScalarString(text)
    folded.fold_pos = positions  # type: ignore[attr-defined]
    return folded
