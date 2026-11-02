"""Rendering one record into its document: front matter from the model, body from a template.

The front matter is serialized by chancellor from `model_serialize`, in the order the model's
`front_matter` names, with the record's `data_hash` last. The template renders the body only
and does no defaulting. The formatter then shapes the body; the front matter stays as
serialized.
"""

import re
from collections.abc import Mapping
from typing import Any

from jinja2 import TemplateError

from .api import FormatContext, Formatter, Model
from .errors import ConfigError
from .registry import Registry
from .yamlio import dump_front_matter

FENCE = "---\n"


def front_matter(record: Model, data_hash: str) -> dict[str, Any]:
    """Front matter mapping of a record's document; empty when the model declares none."""
    keys = type(record).front_matter
    if keys is None:
        return {}
    data = record.model_serialize()
    result = {key: data[key] for key in keys if key in data}
    result["data_hash"] = data_hash
    return result


_REACH = re.compile(r"'(str|dict) object' has no attribute '(data|file_name|path)'")


def reference_hint(message: str) -> str:
    """Cause and fix when a template reads more of another record than a reference allows."""
    match = _REACH.search(message)
    if match is None:
        return ""
    if match.group(1) == "str":
        return (
            "A reference inside a target's data is only an ID: data references reach one hop "
            "(chains of references are not followed yet). Declare a `depends` on a field of "
            "this record and read the record through `refs.<field>`; see the templates "
            "documentation"
        )
    wanted = "data" if match.group(2) == "data" else "name"
    return (
        f'This reference does not expose `{match.group(2)}`: declare `depends="{wanted}"` '
        "on the field (0.1.0:D0032) to read it"
    )


def render_document(
    record: Model,
    template: str,
    *,
    registry: Registry,
    formatter: Formatter,
    context: FormatContext,
    data_hash: str,
    refs: Mapping[str, Any] | None = None,
    extras: Mapping[str, Any] | None = None,
) -> str:
    """The complete document text of a record."""
    try:
        compiled = registry.environment.get_template(template)
        # The template sees the record's own data, its data hash and, under `refs`, exactly
        # what each reference's `depends` declares about its targets (0.1.0:D0032); nothing else.
        body = compiled.render(
            **record.model_serialize(),
            **dict(extras or {}),
            data_hash=data_hash,
            refs=dict(refs or {}),
        )
    except TemplateError as exc:
        hint = reference_hint(str(exc))
        raise ConfigError(
            f"template {template}: {exc}" + (f". {hint}" if hint else "")
        ) from exc
    body = formatter.format(body, context)
    header = front_matter(record, data_hash)
    if not header:
        return body
    return (
        FENCE
        + dump_front_matter(header, context.wrap_width)
        + FENCE
        + "\n"
        + body.lstrip("\n")
    )
