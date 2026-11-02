"""The module key under which chancellor finds its own facets of the data tree.

The top level of the data tree splits by facet: `_api/<module>` and `config/<module>` belong
to one tool each. Chancellor's module key is a variable, not a literal: one default, plus
per-facet overrides that fall back to it. A consumer embedding chancellor under another name
moves one facet or all of them without forking. Code compares against `ModuleKeys`
attributes, never against the default string.
"""

from dataclasses import dataclass, field
from typing import Literal

Facet = Literal["api", "config", "providers", "meta"]

DEFAULT_MODULE = "chancellor"


@dataclass(frozen=True)
class ModuleKeys:
    """Module key per facet: `_api/<api>`, `config/<config>`, `config/<providers>/providers`,
    `meta/<meta>`."""

    default: str = DEFAULT_MODULE
    overrides: dict[Facet, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = set(self.overrides) - {"api", "config", "providers", "meta"}
        if unknown:
            raise ValueError(f"Unknown facets: {', '.join(sorted(unknown))}")

    @property
    def api(self) -> str:
        return self.overrides.get("api", self.default)

    @property
    def config(self) -> str:
        return self.overrides.get("config", self.default)

    @property
    def providers(self) -> str:
        return self.overrides.get("providers", self.default)

    @property
    def meta(self) -> str:
        return self.overrides.get("meta", self.default)
