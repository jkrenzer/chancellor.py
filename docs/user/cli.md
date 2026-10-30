# Command-line reference

This page documents the `chancellor` command, its global options, its subcommands and the exit codes
they return.

## Global options

Global options come before the subcommand: `chancellor [OPTIONS] COMMAND [ARGS]`.

- `--data PATH`: the data file. Without it, chancellor uses `$CHANCELLOR_DATA`, else the nearest
  `chancellor.yaml` in the working directory or above.
- `--set KEY=VALUE`: override a setting below `config/chancellor` for this run, for example
  `--set wrap_width=80` or `--set kinds.decisions.folder=out`. Repeatable. The value is plain YAML,
  without tags or anchors. `providers`, `include`, `loaders` and `data_model` cannot be set this
  way. Overrides enter the configuration digest, so a build with `--set` is reproduced only with the
  same `--set`.
- `-v`, `--verbose`: log the load steps to stderr, including every top-level section of the data
  tree and the configuration sources.
- `--version`: print the installed version and exit.

## Commands

### `chancellor render KIND INPUT`

Validate one record and print its document to stdout; nothing is written. `KIND` is a kind name or
alias: `decisions` (`adr`), `requirements` (`arr`), `specifications` (`asr`), `adr-core`,
`arr-core`, `asr-core`, or a kind a provider contributes. `INPUT` is a YAML file with the record, or
`-` for stdin. Without a data file, the built-in defaults apply. A core document's index is
generated from the project's records of that kind.

### `chancellor schema NAME`

Print a JSON Schema, field descriptions included. `NAME` is a kind or alias, or `config` (the merged
configuration for the loaded providers), `data` (the root model), `provider` (a provider manifest)
or `lock` (the lock file).

### `chancellor hash [ID ...]`

Print the data hash of records, as written into their documents; all records without IDs. An ID may
be bare or absolute (`0.1.0:D0017`); for an older version, chancellor warns and shows the current
record of that ID. The same holds for `explain`.

### `chancellor build [--check] [--strict] [-q]`

Render every document whose inputs changed since the lock, and update the lock. Each document is
listed with its status: `new`, `changed`, `modified` (edited on disk, rendered again), `unchanged`,
`removed` (an orphan chancellor wrote, deleted), `orphan` (kept: edited, or not provably
chancellor's own), or `untracked` (kept: named like a document of its kind but produced by no
record; a warning).

- `--check`: write nothing; exit 3 if anything would change.
- `--strict`: exit 4 if the build has degradations, meaning the same digest could not guarantee the
  same output.
- `-q`, `--quiet`: list only documents that change.

### `chancellor providers`

List the loaded providers in load order, with origin, type, fingerprint and the kinds they
contribute, followed by model overrides and the root model.

### `chancellor explain ID`

Name the digest parts of a record's documents that moved since the lock: its data, what it reads of
other records, files, templates, configuration (including `--set` overrides), the renderer, and the
providers, naming the fingerprint that moved.

### `chancellor doctor`

Check the project: declared providers missing on disk, links that only one side records, records
nothing references, fields without description, a wrap width that differs from the Markdown lint,
orphans and stale documents, and degradations.

### `chancellor lint [PATH ...]`

Run the configured linter (`config/chancellor/linter`). Without a linter, it fails with a
configuration error.

## Exit codes

| Code | Meaning                                                                           |
| ---- | --------------------------------------------------------------------------------- |
| 0    | Success                                                                           |
| 1    | Configuration error, including no linter set under `lint` and command-line misuse |
| 2    | Input invalid: duplicate IDs, dangling references, a record failing its model     |
| 3    | `--check` found drift                                                             |
| 4    | `--strict` found degradations                                                     |
| 5    | The linter reported problems                                                      |
| 6    | Internal error                                                                    |

Each command's `--help` lists the codes it can return. `doctor` exits 1 for problems that need
action and 2 for problems in the record data.
