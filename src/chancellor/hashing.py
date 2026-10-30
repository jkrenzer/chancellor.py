"""Digests of records and documents.

`data_hash` is the record's own canonical data, identical standalone and in the project; the
schema that validated it never enters it. A document's `input_hash` is the digest of its
parts, each stored in the lock so `explain` can name the one that moved:

- `data`: the record's own `data_hash`;
- `refs`: what the template sees of other records, and nothing more (0.1.0:D0032): the `refs`
  context, in which each reference exposes only what its `depends` declares (the ID, also the
  file name and path, or also the target's data; one hop, never transitive), plus the record's
  generated fields, such as a core document's index;
- `files`: bytes of hashed file refs (no built-in kind declares any yet);
- `templates`: source strings of every template reachable from the document's;
- `meta`: the record-set version and the absolute-ID format, which templates can show;
- `config`: the digest of the whole validated `config/chancellor`;
- `api`: the data-tree format version and the renderer fingerprint: chancellor's version (plus
  its source digest in an editable install), the Python implementation and version, and the
  installed versions of every distribution that shapes the output (0.1.0:D0017);
- `providers`: the same for every document (0.1.0:D0018): the resolved provider set and every
  fingerprint of the build (providers, root model, model overrides, import-path code, the
  kinds' schema digests). Any change rebuilds everything chancellor owns.
"""

import platform
import re
import sys
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, distribution, version
from importlib.resources import files
from typing import Any

from . import providers
from .api import Degradation, Generated, Model, marked_fields
from .canonical import digest_of
from .codeload import source_digest
from .config import DATA_API_VERSION
from .project import Project

PARTS = ("data", "refs", "files", "templates", "meta", "config", "api", "providers")


def renderer_version() -> str:
    """Chancellor's own version string, recorded unchanged."""
    try:
        return version("chancellor")
    except PackageNotFoundError:
        return "unknown"


OUTPUT_DISTRIBUTIONS = (
    "jinja2",
    "mdformat",
    "mdformat-gfm",
    "ruamel.yaml",
    "pydantic",
    "rfc8785",
)
"""Distributions whose code shapes the bytes chancellor writes: templating, Markdown formatting,
front matter, validation and serialization, canonical JSON. Their runtime requirements count
too (0.1.0:D0017)."""


def renderer_fingerprint() -> str:
    """What the `api` part records about the code that ran (0.1.0:D0017: same digest, same
    bytes): chancellor's version, plus its source digest when it is an editable install;
    the Python implementation and version; the installed versions of every distribution that
    shapes the output and of their requirements."""
    version_string = renderer_version()
    if providers.distribution_info("chancellor")[1]:
        version_string += f" source {source_digest(files('chancellor'))}"
    python = f"{platform.python_implementation()} {sys.version_info[0]}.{sys.version_info[1]}"
    return digest_of(
        {
            "chancellor": version_string,
            "python": python,
            "dependencies": output_dependencies(),
        }
    )


def output_dependencies() -> dict[str, str]:
    """Installed version of each output distribution and of its runtime requirements, by
    normalized name. A requirement that is not installed is left out (it cannot run)."""
    found: dict[str, str] = {}
    pending = list(OUTPUT_DISTRIBUTIONS)
    while pending:
        name = pending.pop()
        key = re.sub(r"[-_.]+", "-", name).lower()
        if key in found:
            continue
        try:
            dist = distribution(name)
        except PackageNotFoundError:
            continue
        found[key] = dist.version
        for requirement in dist.requires or []:
            requirement_name, _, marker = requirement.partition(";")
            if "extra" in marker:
                continue
            pending.append(
                re.split(r"[\s<>=!~\[(]", requirement_name.strip(), maxsplit=1)[0]
            )
    return dict(sorted(found.items()))


def data_hash(record: Model) -> str:
    """Digest of a record's own canonical data."""
    return digest_of(record.model_canonicalize())


@dataclass
class Environment:
    """Digest parts shared by every document of one build."""

    api: str
    config: str
    membership: list[list[str]]
    meta: str
    """Digest of the record-set version and the absolute-ID format (0.1.0:D0036)."""
    fingerprints: dict[str, str]
    """Every fingerprint of the build: providers, `data_model`, `model:<kind>` overrides,
    `code:<address>` (import-path formatters, linters, loaders), `schema:<kind>` digests."""
    hashes: dict[str, str] = field(default_factory=dict)
    degradations: list[Degradation] = field(default_factory=list)

    @classmethod
    def of(cls, project: Project) -> "Environment":
        registry = project.registry
        membership = [
            [p.name, p.origin, "code" if p.code else "declarative"]
            for p in registry.providers
        ]
        fingerprints = registry.fingerprints()
        if project.root_model is not None:
            membership.append(["data_model", project.root_model.origin, "code"])
            fingerprints["data_model"] = project.root_model.fingerprint
        for kind, override in project.model_overrides.items():
            fingerprints[f"model:{kind}"] = override.fingerprint
        fingerprints.update(project.code_fingerprints)
        for kind, schema in registry.model_fingerprints().items():
            fingerprints[f"schema:{kind}"] = schema
        return cls(
            api=digest_of(
                {"data_api": DATA_API_VERSION, "renderer": renderer_fingerprint()}
            ),
            config=project.config_digest,
            meta=digest_of(
                {
                    "version": project.record_set_version,
                    "absolute_id": project.config.versioning.absolute_id,
                }
            ),
            membership=membership,
            fingerprints=dict(sorted(fingerprints.items())),
            hashes={
                rid: data_hash(record) for rid, (_, record) in project.records.items()
            },
            degradations=list(project.degradations),
        )

    @property
    def providers_digest(self) -> str:
        """Digest of the provider set itself: names, origins and kinds of fingerprint."""
        return digest_of(self.membership)

    @property
    def providers_part(self) -> str:
        """The `providers` part, the same for every document (0.1.0:D0018): the set and every
        fingerprint. Any change in either rebuilds everything chancellor owns."""
        return digest_of({"set": self.membership, "fingerprints": self.fingerprints})


@dataclass
class DocumentInputs:
    """The digest parts of one document."""

    parts: dict[str, str]

    @property
    def input_hash(self) -> str:
        return digest_of(self.parts)


def dependency_context(project: Project, record: Model) -> dict[str, Any]:
    """Everything a document's template sees that is not the record's own data: its generated
    fields (a core document's index) and the `refs` context. The `refs` part digests exactly
    this, so content changes that cannot reach the document do not rebuild it (0.1.0:D0032).
    """
    serialized = record.model_serialize()
    generated = {
        name: serialized.get(name)
        for name in sorted(marked_fields(type(record), Generated))
    }
    # chains (deferred, 0.1.0:D0033): the refs digest covers whatever `ref_context` exposes, so a
    # chain implementation that nests followed targets there is digested here unchanged.
    return {"generated": generated, "refs": project.ref_context(record)}


def document_inputs(
    project: Project,
    environment: Environment,
    record: Model,
    template: str,
) -> DocumentInputs:
    """Digest parts of the document rendered from `record` with `template`."""
    sources, dynamic = project.registry.template_closure(template)
    if dynamic:
        environment.degradations.append(
            Degradation(
                "dynamic-template-reference",
                template,
                "a template reference is computed at render time and cannot be followed",
            )
        )
    parts = {
        "data": environment.hashes.get(record.id) or data_hash(record),
        "refs": digest_of(dependency_context(project, record)),
        "files": digest_of([]),
        "templates": digest_of(sources),
        # The record-set version enters every document, so a version bump rebuilds everything
        # (0.1.0:D0036): simpler and more robust than finding the templates that show it.
        "meta": environment.meta,
        "config": environment.config,
        "api": environment.api,
        "providers": environment.providers_part,
    }
    return DocumentInputs(parts=parts)
