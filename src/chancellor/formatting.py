"""Built-in formatter types: `builtin.mdformat` and `builtin.none`."""

import mdformat
from pydantic import Field

from .api import FormatContext, Formatter


class MdformatFormatter(Formatter):
    """Wraps Markdown with mdformat and GitHub Flavored Markdown, without code formatters.

    Long indivisible content such as URLs, inline code, headings, table rows and code blocks
    may exceed the width rather than being split in a way that changes its meaning.
    """

    wrap: int | None = Field(
        default=None, gt=0, description="Wrap width; defaults to `wrap_width`."
    )

    def format(self, text: str, context: FormatContext) -> str:
        return mdformat.text(
            text,
            options={"wrap": self.wrap or context.wrap_width},
            extensions={"gfm"},
            codeformatters=(),
        )


class NoneFormatter(Formatter):
    """Leaves rendered text as the template produced it."""

    def format(self, text: str, context: FormatContext) -> str:
        del context
        return text
