"""Loading consumer code named in configuration, and fingerprinting it (0.1.0:D0005, 0.1.0:D0030).

A reference is either a file path relative to the project root, `arch/models/records.py:Name`,
or an importable module, `package.module:Name`. A file is loaded under a name that includes the
digest of its source, so a changed file is a new module and a long-running process never serves
a stale one. A file is fingerprinted by its bytes; an importable module by its distribution's
version, or by its bytes when no distribution owns it.
"""

import ast
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import sys
from dataclasses import dataclass
from importlib.metadata import (
    PackageNotFoundError,
    distribution,
    packages_distributions,
)
from importlib.resources.abc import Traversable
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import BaseModel

from .api import Degradation
from .canonical import digest, digest_of
from .errors import ConfigError
from .paths import confine, relative


def distribution_info(name: str) -> tuple[str | None, bool]:
    """Version of an installed distribution and whether it is an editable install."""
    try:
        dist = distribution(name)
    except PackageNotFoundError:
        return None, False
    direct_url = dist.read_text("direct_url.json")
    editable = False
    if direct_url:
        try:
            editable = bool(json.loads(direct_url).get("dir_info", {}).get("editable"))
        except (ValueError, AttributeError):
            editable = False
    return dist.version, editable


def load_file_module(path: Path, namespace: str) -> tuple[ModuleType, bytes]:
    """Load a Python file as a module named after `namespace` and its source digest."""
    source = path.read_bytes()
    tag = hashlib.sha256(source).hexdigest()[:16]
    qualified = f"{namespace}.m{tag}"
    if qualified in sys.modules:
        return sys.modules[qualified], source
    spec = importlib.util.spec_from_file_location(qualified, path)
    if spec is None or spec.loader is None:
        raise ConfigError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    try:
        # Compile the bytes just read and fingerprinted, never cached bytecode: a `.pyc` is
        # trusted by modification time and size, which an edit of the same length can keep.
        code = compile(source, str(path), "exec")
        exec(code, module.__dict__)  # pylint: disable=exec-used
    except Exception as exc:
        del sys.modules[qualified]
        raise ConfigError(f"{path} failed to load: {exc}") from exc
    return module, source


@dataclass(frozen=True)
class CodeObject:
    """An object loaded from consumer code, with where it came from and its code fingerprint."""

    reference: str
    obj: Any
    origin: str
    code: str
    degradations: tuple[Degradation, ...] = ()


def is_file_reference(module_part: str) -> bool:
    return "/" in module_part or module_part.endswith(".py")


def load_object(root: Path, reference: str, setting: str) -> CodeObject:
    """Load `path/to/file.py:Name` (relative to `root`) or `package.module:Name`."""
    module_part, _, attribute = reference.rpartition(":")
    if not module_part or not attribute:
        raise ConfigError(
            f"{setting}: {reference!r} must be written path/to/file.py:Name or module:Name"
        )
    if is_file_reference(module_part):
        path = confine(root, module_part, setting=setting)
        if not path.is_file():
            raise ConfigError(f"{setting}: {module_part} does not exist")
        rel = relative(root, path)
        namespace = "_chancellor_project." + rel.removesuffix(".py").replace("/", ".")
        try:
            module, source = load_file_module(path, namespace)
        except ConfigError as exc:
            raise ConfigError(f"{setting}: {exc}") from exc
        del source
        origin, label = rel, f"file:{rel}"
    else:
        try:
            module = importlib.import_module(module_part)
        except ImportError as exc:
            raise ConfigError(f"{setting}: cannot import {module_part}: {exc}") from exc
        dists = packages_distributions().get(module_part.partition(".")[0], [])
        origin, label = (dists[0] if dists else module_part), module_part
    try:
        obj = getattr(module, attribute)
    except AttributeError as exc:
        raise ConfigError(f"{setting}: {module_part} has no {attribute}") from exc
    fingerprint = code_fingerprint(module, label=label)
    return CodeObject(
        reference=reference,
        obj=obj,
        origin=origin,
        code=fingerprint.value,
        degradations=fingerprint.degradations,
    )


DERIVED_SUFFIXES = (".pyc", ".pyo")
"""Files derived from others in the tree; they never enter a source digest."""

EXTENSION_SUFFIXES = (".so", ".pyd", ".dylib", ".dll")
"""Compiled code: its behaviour also depends on libraries outside the tree, so a digest over
its bytes is not complete (0.1.0:D0017)."""


@dataclass(frozen=True)
class SourceDigest:
    """Digest of a package tree, and whether it covers everything that can change behaviour."""

    value: str
    complete: bool
    reason: str = ""


_DIGESTS: dict[str, SourceDigest] = {}


def reset_source_digests() -> None:
    """Forget the digests of the current load; the next request walks and reads again. The
    import system's directory caches are invalidated too, so a module file created since the
    last load is found, which matters in long-running processes."""
    _DIGESTS.clear()
    _FINGERPRINTS.clear()
    importlib.invalidate_caches()


def source_digest(root: Traversable) -> str:
    """Digest of every file below `root`, by relative path and content (0.1.0:D0017)."""
    return tree_digest(root).value


def tree_digest(root: Traversable) -> SourceDigest:
    """Digest of every file below `root`, and whether it is complete (0.1.0:D0017).

    Used where a version string cannot be trusted to name the code, such as an editable
    install: any edit to a module, template, manifest or data file changes it. Files are read,
    not judged by modification time and size, which can miss an edit of the same length.
    `__pycache__` and compiled bytecode are skipped as derived. A compiled extension or an
    unreadable file makes the digest incomplete. The result is kept until
    `reset_source_digests`, which every project load calls.
    """
    key = str(root)
    if key in _DIGESTS:
        return _DIGESTS[key]
    entries: dict[str, str] = {}
    gaps: list[str] = []

    def walk(node: Traversable, prefix: str) -> None:
        for child in sorted(node.iterdir(), key=lambda item: item.name):
            if child.is_dir():
                if child.name != "__pycache__":
                    walk(child, f"{prefix}{child.name}/")
            elif not child.name.endswith(DERIVED_SUFFIXES):
                if child.name.endswith(EXTENSION_SUFFIXES):
                    gaps.append(f"compiled extension {prefix}{child.name}")
                try:
                    entries[prefix + child.name] = digest(child.read_bytes())
                except OSError as exc:
                    gaps.append(
                        f"unreadable {prefix}{child.name} ({exc.strerror or exc})"
                    )

    walk(root, "")
    _DIGESTS[key] = SourceDigest(digest_of(entries), not gaps, "; ".join(gaps))
    return _DIGESTS[key]


def model_fingerprint(models: list[type[BaseModel]], code: str) -> str:
    """Fingerprint of model classes: the JSON Schemas they emit plus their code (0.1.0:D0005)."""
    schemas = [model.model_json_schema() for model in models]
    return digest_of({"schema": digest_of(schemas, allow_float=True), "code": code})


# Code fingerprints (0.1.0:D0031): one path for every code reference


RENDERER_PACKAGE = __name__.partition(".")[0]
"""Chancellor's own top-level package; its code is covered by the renderer fingerprint."""

IMPORT_ERRORS = frozenset({"ImportError", "ModuleNotFoundError"})

_FINGERPRINTS: dict[str, "CodeFingerprint"] = {}


@dataclass(frozen=True)
class CodeFingerprint:
    """Fingerprint of a module and the code it reaches, and why it may be unreliable."""

    value: str
    degradations: tuple[Degradation, ...] = ()


def code_fingerprint(
    module: ModuleType, *, label: str | None = None
) -> CodeFingerprint:
    """Fingerprint of `module` by where its code comes from (0.1.0:D0031, 0.1.0:D0005, 0.1.0:D0021).

    - A module of an installed distribution: the distribution's exact version string; when the
      install is editable, also a source digest of its top-level package and an
      `editable-install` degradation.
    - Any other module: the digest of its own source and of every module it imports, found
      statically and without executing anything. The walk stops at the standard library, at
      installed distributions (which contribute their fingerprint) and at chancellor itself
      (covered by the renderer fingerprint). Package `__init__` files on the way are included.
      An import that cannot be resolved, or one whose name is computed, degrades the
      fingerprint (`unfingerprinted-code`); an optional import guarded by `except ImportError`
      that does not resolve is recorded as absent instead. Not covered: the Python version and
      files a module reads at runtime.

    `label` names the module in the digest when its import name is not stable, such as a file
    loaded under a digest-derived name. Results are memoized until `reset_source_digests`.
    """
    key = label or module.__name__
    if key not in _FINGERPRINTS:
        closure = _Closure()
        closure.add_root(module, key)
        _FINGERPRINTS[key] = closure.result()
    return _FINGERPRINTS[key]


class _Closure:
    """Walks the static import closure of loose code."""

    def __init__(self) -> None:
        self.modules: dict[str, str] = {}
        self.distributions: dict[str, str] = {}
        self.absent: set[str] = set()
        self.unresolved: set[str] = set()
        self.dynamic: set[str] = set()
        self.degradations: list[Degradation] = []
        self._seen: set[str] = set()
        self._owners = packages_distributions()

    def result(self) -> CodeFingerprint:
        value = digest_of(
            {
                "modules": dict(sorted(self.modules.items())),
                "distributions": dict(sorted(self.distributions.items())),
                "absent": sorted(self.absent),
                "unresolved": sorted(self.unresolved),
                "dynamic": sorted(self.dynamic),
            }
        )
        return CodeFingerprint(value, tuple(self.degradations))

    def add_root(self, module: ModuleType, key: str) -> None:
        name = module.__name__
        if self._kind(name) != "loose" and not name.startswith("_chancellor_"):
            self._seen.add(name)
            self._distribution(name)
            return
        spec = getattr(module, "__spec__", None)
        path = spec.origin if spec is not None else None
        if not path or not Path(path).is_file():
            self._degrade(key, f"module {name} has no source file")
            return
        self._seen.add(name)
        source = Path(path).read_bytes()
        self.modules[key] = digest(source)
        package = module.__package__ if not name.startswith("_chancellor_") else None
        self._walk(source, path, package, key)

    # classification

    def _kind(self, name: str) -> str:
        top = name.partition(".")[0]
        if top in sys.stdlib_module_names or top in sys.builtin_module_names:
            return "stdlib"
        if top == RENDERER_PACKAGE:
            return "renderer"
        if top in self._owners:
            return "distribution"
        return "loose"

    def _owner(self, name: str) -> str:
        """Distribution owning module `name`. A namespace top-level name such as `ruamel` can
        be shared by several distributions; then their file lists decide."""
        candidates = sorted(set(self._owners[name.partition(".")[0]]))
        if len(candidates) > 1:
            parts = name.split(".")
            for depth in range(len(parts), 1, -1):
                prefix = "/".join(parts[:depth])
                for candidate in candidates:
                    files = distribution(candidate).files or []
                    if any(
                        str(f).startswith(prefix + "/") or str(f) == prefix + ".py"
                        for f in files
                    ):
                        return candidate
        return candidates[0]

    def _distribution(self, name: str) -> None:
        top = name.partition(".")[0]
        if self._kind(name) != "distribution":
            return
        dist = self._owner(name)
        if dist in self.distributions:
            return
        version, editable = distribution_info(dist)
        value = f"version:{version}"
        if editable:
            location = _package_location(_find_spec(top))
            tree = tree_digest(location) if location is not None else None
            if tree is not None:
                value += f" source {tree.value}"
            if tree is None or not tree.complete:
                # 0.1.0:D0017: only an editable install that cannot be hashed completely degrades.
                reason = (
                    tree.reason
                    if tree is not None
                    else "its source tree cannot be found"
                )
                self.degradations.append(
                    Degradation(
                        "editable-install",
                        dist,
                        f"distribution {dist} is an editable install whose source cannot be "
                        f"fully hashed: {reason}",
                    )
                )
        self.distributions[dist] = value

    # walking

    def _visit(self, name: str, guarded: bool, importer: str) -> None:
        if name in self._seen:
            return
        kind = self._kind(name)
        if kind in ("stdlib", "renderer"):
            self._seen.add(name)
            return
        if kind == "distribution":
            self._seen.add(name)
            self._distribution(name)
            return
        parts = name.split(".")
        for depth in range(1, len(parts)):
            self._visit(".".join(parts[:depth]), guarded, importer)
        spec = _find_spec(name)
        self._seen.add(name)
        if spec is None:
            if guarded:
                self.absent.add(name)
            else:
                self.unresolved.add(name)
                self._degrade(importer, f"import {name} cannot be resolved")
            return
        origin = spec.origin
        if not origin or not origin.endswith(".py") or not Path(origin).is_file():
            return  # namespace package or extension module: nothing to read
        source = Path(origin).read_bytes()
        self.modules[name] = digest(source)
        package = (
            name
            if spec.submodule_search_locations is not None
            else name.rpartition(".")[0]
        )
        self._walk(source, origin, package, name)

    def _walk(
        self, source: bytes, path: str, package: str | None, importer: str
    ) -> None:
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError:
            self._degrade(importer, f"{path} cannot be parsed")
            return
        found, computed = _imports(tree, package)
        for line in computed:
            self.dynamic.add(f"{importer}:{line}")
            self._degrade(importer, f"import name computed at runtime (line {line})")
        for name, guarded in found:
            if name.startswith("."):
                self._degrade(importer, f"relative import {name} without a package")
                continue
            self._visit(name, guarded, importer)

    def _degrade(self, subject: str, message: str) -> None:
        self.degradations.append(Degradation("unfingerprinted-code", subject, message))


def _find_spec(name: str) -> Any:
    """Spec of `name` without importing anything: a module already loaded keeps its spec;
    otherwise each level is looked up in its parent's search locations."""
    loaded = sys.modules.get(name)
    if loaded is not None and getattr(loaded, "__spec__", None) is not None:
        return loaded.__spec__
    parts = name.split(".")
    search: Any = None
    spec: Any = None
    for depth in range(1, len(parts) + 1):
        current = ".".join(parts[:depth])
        loaded = sys.modules.get(current)
        if loaded is not None and getattr(loaded, "__spec__", None) is not None:
            spec = loaded.__spec__
        else:
            spec = importlib.machinery.PathFinder.find_spec(current, search)
        if spec is None:
            return None
        search = spec.submodule_search_locations
        if search is None and depth < len(parts):
            return None
    return spec


def _package_location(spec: Any) -> Path | None:
    if spec is None:
        return None
    if spec.submodule_search_locations:
        return Path(list(spec.submodule_search_locations)[0])
    return Path(spec.origin).parent if spec.origin else None


def _imports(
    tree: ast.AST, package: str | None
) -> tuple[list[tuple[str, bool]], list[int]]:
    """Module names imported anywhere in `tree`, each with whether an `except ImportError` (or
    `ModuleNotFoundError`) handler guards it; and the lines of imports with computed names.
    """
    found: list[tuple[str, bool]] = []
    computed: list[int] = []

    def resolve(level: int, module: str | None) -> str | None:
        if level == 0:
            return module
        if not package:
            return "." * level + (module or "")
        try:
            return importlib.util.resolve_name("." * level + (module or ""), package)
        except ImportError:
            return "." * level + (module or "")

    def guards(handler: ast.ExceptHandler) -> bool:
        names = (
            handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        )
        return any(isinstance(n, ast.Name) and n.id in IMPORT_ERRORS for n in names)

    def visit(node: ast.AST, guarded: bool) -> None:
        if isinstance(node, ast.Try):
            inner = guarded or any(guards(handler) for handler in node.handlers)
            for child in node.body:
                visit(child, inner)
            for child in [*node.handlers, *node.orelse, *node.finalbody]:
                visit(child, guarded)
            return
        if isinstance(node, ast.Import):
            found.extend((alias.name, guarded) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = resolve(node.level, node.module)
            if base:
                found.append((base, guarded))
                if not base.startswith("."):
                    for alias in node.names:
                        candidate = f"{base}.{alias.name}"
                        if (
                            alias.name != "*"
                            and _find_spec_quiet(candidate) is not None
                        ):
                            found.append((candidate, guarded))
        elif isinstance(node, ast.Call) and _is_import_call(node.func):
            argument = node.args[0] if node.args else None
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                found.append((argument.value, guarded))
            else:
                computed.append(getattr(node, "lineno", 0))
        for child in ast.iter_child_nodes(node):
            visit(child, guarded)

    visit(tree, False)
    return found, computed


def _find_spec_quiet(name: str) -> Any:
    try:
        return _find_spec(name)
    except (ImportError, ValueError):
        return None


def _is_import_call(func: ast.expr) -> bool:
    if isinstance(func, ast.Name):
        return func.id in ("__import__", "import_module")
    return isinstance(func, ast.Attribute) and func.attr == "import_module"
