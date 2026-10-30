# Configuration reference

This page lists every configuration setting chancellor reads, where it is read from, and its
default.

## Where settings come from

Settings below `config/chancellor` arrive from several sources; a higher one wins:

1. `--set KEY=VALUE` on the command line, e.g. `chancellor --set wrap_width=80 build`. `KEY` is
   dotted (`kinds.decisions.folder`); `VALUE` is plain YAML, without tags or anchors.
2. The environment: `CHANCELLOR_WRAP_WIDTH=80`, nested keys joined with `__`.
3. The config loaders listed in `config/chancellor/loaders`, the first one highest. The default,
   `builtin.data_file`, reads the data file. A provider or an import path (`path/to/file.py:Class`)
   can add loaders, written as a type or as a mapping with `type` and the loader's own arguments.
4. A supplied root model's configuration defaults (see below), then the providers' and chancellor's
   own defaults.

`providers`, `include`, `loaders` and `data_model` are read first, from the main data file only.
Under `kinds`, each kind's settings merge field by field: a source that sets only
`kinds.decisions.folder` keeps that kind's other settings from the levels below. Every other nested
value (`formatter`, `linter`, `loaders`, `providers`, `include`) is replaced as a whole by the
highest source that sets it. Every setting enters the configuration digest, `--set` values too: a
build with `--set` records them in the lock, and a later `build --check` without them reports drift,
which `explain` names. The digest records `--set` overrides as such: a build made with
`--set wrap_width=60` is reproduced only with the same `--set`; the same value from the environment
or the data file counts as drift.

## Where record data lives

Records live in the data file `chancellor.yaml`, in further files listed under
`config/chancellor/include`, or, per kind, in a data file of its own:

```yaml
config:
  chancellor:
    kinds:
      decisions:
        data: arch/data/decisions.yaml   # holds the kind's section: core and records
        folder: arch/decisions           # where the documents are written
```

A kind's data file holds that kind's section only, so it cannot also be listed under `include`.
Moving records between these files changes no digest. A file shared by several kinds, with a key
path to each kind's section, is planned for a later version.

## Versions and absolute IDs

The record set as a whole can carry a version, kept as data in the `meta` facet next to `_api` and
`config`:

```yaml
meta:
  chancellor:
    version: "0.1.0"
config:
  chancellor:
    versioning:
      scheme: semver              # semver, pep440, free (the default), or a provider's scheme
      absolute_id: "{version}:{id}"
```

With a scheme that checks versions (`semver`, `pep440`), chancellor checks that the record-set
version and every revision version parse under the scheme, and that a record's revision versions
increase from oldest to newest. With `free`, only the record models' own rules apply. A provider can
contribute further schemes, and a project can name one by import path (`path/to/file.py:Class`), as
for formatters and linters.

An absolute ID combines the record-set version and a record ID, `0.1.0:D0017` with the default
format. Use absolute IDs when referring to records from outside the record set, such as in code,
commit messages or other projects. Inside the record data, a bare ID (`D0017`) means the current
version; an absolute ID of the current version means the same. An absolute ID of an older version is
a historic reference: it is not checked against the current data, chancellor warns about it,
`chancellor doctor` lists every one, and templates can mark it. When the record set's version
increases, absolute IDs of the previous version become historic by themselves. An absolute ID of a
newer version than the data is invalid.

`chancellor explain` and `chancellor hash` accept absolute IDs too; for a historic one they warn and
show the current record of that ID.

Templates see the record-set version as `meta.version` and each record's absolute ID as
`absolute_id`. A change of the version or of the format rebuilds every document.

## Looking into problems with the data file

Chancellor reads every top-level section of the data tree. Sections it does not own, such as another
tool's kinds or a misspelled kind name, are ignored without an error. To see how each section was
read, raise the log level with `-v` (`--verbose`) before the command:

```bash
chancellor -v build --check
```

The log names every section, the provider of its kind or that it was ignored, and the files it came
from, followed by the configuration sources in the order they apply. `chancellor doctor` also lists
ignored sections.

## Supplying a root model

A project can validate its data tree with its own Pydantic root model, named in
`config/chancellor/data_model` as `path/to/file.py:Class` (relative to the project root) or
`module:Class`. Build it from the bases in `chancellor.api`, and it inherits every field and its
default: `_api`, `config`, and the configuration with all of chancellor's defaults. Declare one
field per record kind, typed with that kind's section.

For the built-in kinds the sections are ready-made:

```python
from chancellor.api import ProjectModel
from chancellor.builtin.jkrenzer.models import DecisionSection, RequirementSection


class Catalogue(ProjectModel):
    decisions: DecisionSection | None = None
    requirements: RequirementSection | None = None
```

Kinds the root model does not declare are validated by chancellor's generated models as before.
Output folders, templates and every other setting stay configurable as usual.

To change a configuration default or add a setting of your own, subclass `ChancellorConfig` and the
`ConfigTree` that holds it, and use `default_factory`:

```python
from pydantic import Field

from chancellor.api import ChancellorConfig, ConfigTree


class MyConfig(ChancellorConfig):
    wrap_width: int = 80
    team: str = Field(default="docs", description="Owning team.")


class MyConfigTree(ConfigTree):
    chancellor: MyConfig = Field(default_factory=MyConfig)


class Configured(Catalogue):
    config: MyConfigTree = Field(default_factory=MyConfigTree)
```

Defaults for a kind work the same way: `kinds = {"decisions": KindConfig(folder="docs/adr")}` in
`MyConfig` changes the decisions' folder and keeps every other setting of that kind, and a model
override set there takes the same checks as one in the data file.

Chancellor builds its configuration on top of `MyConfig`, so the added setting and any validator
take effect, appear in `chancellor schema config`, and enter the configuration digest. What the data
file sets wins over the class defaults, and the environment (`CHANCELLOR_*`) wins over both. A
record section's models must be subclasses of the kind's built-in models, so the kind's templates
keep working.

## How chancellor fingerprints code

Every piece of code a build uses is fingerprinted, so that changing it rebuilds the documents:
providers and their models, model overrides, a root model, and formatter, linter and loader types
named by import path. Any change in any fingerprint rebuilds every document, and
`chancellor explain ID` names the fingerprint that moved. The fingerprint depends on where the code
comes from:

- **An installed distribution:** its exact version string. No degradation.
- **An editable install** (`pip install -e`, `poetry install`): its version plus a digest of all its
  package's files. No degradation while every file can be hashed; a compiled extension or an
  unreadable file makes it an `editable-install` degradation.
- **A file in the project, or a module no distribution owns:** a digest of its source and of every
  module it imports. No degradation.
- **Code whose imports cannot all be followed:** a digest of what could be followed, and an
  `unfingerprinted-code` degradation.

Imports are found by reading the source, never by running it: imports at module level and inside
functions alike, with the package `__init__.py` files on the way. The walk stops at the standard
library, at installed distributions (which count by their version) and at chancellor itself. An
optional import guarded by `except ImportError` that is not installed is recorded as absent, so
installing it later rebuilds. An import that cannot be resolved, or one whose name is computed at
runtime, makes the fingerprint incomplete and is reported as a degradation; `build --strict` fails
on degradations.

The renderer's own fingerprint covers chancellor's version (and its source, in an editable install),
the Python version, and the installed versions of the libraries that shape the output. So the same
digest means the same bytes from the same input; `build --strict` fails only where that cannot be
guaranteed. Files that code reads while it runs are outside every fingerprint.
