"""Model subclasses for the override tests, importable as `tests.traced`."""

from chancellor.builtin.jkrenzer.models import Decision, DecisionCore, Document, Text


def after(keys, anchor, key):
    """`keys` with `key` inserted right after `anchor`."""
    items = list(keys)
    items.insert(items.index(anchor) + 1, key)
    return tuple(items)


class TracedDecision(Decision):
    """A decision with a required trace to design items."""

    front_matter = after(Decision.front_matter, "tags", "source")

    source: list[Text]


class NotADecision(Document):
    """Shares a base with Decision but does not subclass it."""


class TracedCore(DecisionCore):
    """The decision core, unchanged apart from being a subclass."""
