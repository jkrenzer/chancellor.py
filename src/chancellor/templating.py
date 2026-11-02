"""The Jinja2 environment and template loading.

Templates are addressed as `<provider>/<name>`. Each provider's template folder is reached
through `TraversableLoader`, which reads from a package resource or a plain folder alike, so
the built-in templates take the same path as a local provider's. A `PrefixLoader` routes the
provider prefix; nothing shadows anything.

The environment stays open for later rendering modes: callers may register further
globals and filters, and a template may emit Jinja2 for a later pass with `{% raw %}`.
"""

from collections.abc import Callable, Mapping
from importlib.resources.abc import Traversable
from typing import Any

from jinja2 import (
    BaseLoader,
    Environment,
    PrefixLoader,
    StrictUndefined,
    TemplateNotFound,
    Undefined,
    meta,
)


class TraversableLoader(BaseLoader):
    """Loads templates from a `Traversable`: a package resource folder or a `Path`."""

    def __init__(self, root: Traversable) -> None:
        self.root = root
        self._sources: dict[str, str] = {}

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str | None, Callable[[], bool]]:
        if template not in self._sources:
            parts = [part for part in template.split("/") if part]
            if not parts or any(part in (".", "..") for part in parts):
                raise TemplateNotFound(template)
            node = self.root.joinpath(*parts)
            if not node.is_file():
                raise TemplateNotFound(template)
            # Sources are read once per load; a build sees one consistent set.
            self._sources[template] = node.read_text("utf-8")
        return self._sources[template], None, lambda: True

    def list_templates(self) -> list[str]:
        found: list[str] = []

        def walk(node: Traversable, prefix: str) -> None:
            for child in sorted(node.iterdir(), key=lambda item: item.name):
                if child.is_dir():
                    walk(child, f"{prefix}{child.name}/")
                elif child.name.endswith(".j2"):
                    found.append(prefix + child.name)

        walk(self.root, "")
        return found


def required_text(value: Any, name: str) -> str:
    """Template filter: reject missing, null, empty or non-string text."""
    if isinstance(value, Undefined) or not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def required_list(value: Any, name: str) -> list[Any]:
    """Template filter: reject missing, null, empty or non-list collections."""
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a nonempty list")
    return value


def make_environment(roots: Mapping[str, Traversable]) -> Environment:
    """Strict environment over the template folders of the given providers."""
    environment = Environment(
        loader=PrefixLoader(
            {name: TraversableLoader(root) for name, root in roots.items()},
            delimiter="/",
        ),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    environment.filters.update(required_text=required_text, required_list=required_list)
    return environment


def template_closure(
    environment: Environment, name: str
) -> tuple[dict[str, str], bool]:
    """Source of `name` and every template it reaches, from the loader; and whether some
    reference could not be followed because it is computed at render time."""
    assert environment.loader is not None
    sources: dict[str, str] = {}
    dynamic = False
    pending = [name]
    while pending:
        current = pending.pop()
        if current in sources:
            continue
        source = environment.loader.get_source(environment, current)[0]
        sources[current] = source
        for reference in meta.find_referenced_templates(environment.parse(source)):
            if reference is None:
                dynamic = True
            else:
                pending.append(reference)
    return dict(sorted(sources.items())), dynamic
