"""Command line interface.

Every command returns a code from the exit-code table in `chancellor.errors` (0.1.0:D0010); the
table is printed in the help, and each command's help names the codes it can return.
Command-line misuse is a configuration error (1), so it cannot be mistaken for invalid
input (2).
"""

import json
import logging
import sys
import traceback
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError

from . import __version__
from .api import LintContext, ProviderManifest
from .build import explain as explain_record
from .build import run as run_build
from .config import config_model, parse_overrides
from .doctor import diagnose
from .errors import (
    EXIT_CODE_HELP,
    ChancellorError,
    ConfigError,
    ExitCode,
    InputError,
    ResultCode,
)
from .hashing import data_hash
from .lock import Lock
from .paths import template_suffix
from .project import Project, config_class
from .rendering import render_document
from .yamlio import parse as parse_yaml

EPILOG = "\b\nExit codes:\n" + EXIT_CODE_HELP

app = typer.Typer(
    name="chancellor",
    help=(
        "Generate documents from the project data tree: validate records against their "
        "models, render them with their kind's templates and keep them in step with the "
        "data, incrementally."
    ),
    epilog=EPILOG,
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)

DataOption = Annotated[
    Path | None,
    typer.Option(
        "--data",
        help="Data file; default: $CHANCELLOR_DATA, else the nearest chancellor.yaml upwards.",
        show_default=False,
    ),
]


class SchemaTarget(StrEnum):
    """Schemas besides the record kinds."""

    CONFIG = "config"
    DATA = "data"
    PROVIDER = "provider"
    LOCK = "lock"


class _StderrHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Writes to whatever `sys.stderr` is when a record is emitted."""

    def __init__(self) -> None:
        super().__init__()

    @property  # type: ignore[override]
    def stream(self) -> Any:
        return sys.stderr

    @stream.setter
    def stream(self, value: Any) -> None:
        del value


def _show_on_stderr(name: str, level: int, form: str) -> None:
    """Show a logger's records on stderr from `level` up, also without `-v`."""
    target = logging.getLogger(name)
    if not any(isinstance(h, _StderrHandler) for h in target.handlers):
        handler = _StderrHandler()
        handler.setFormatter(logging.Formatter(form))
        target.addHandler(handler)
        target.propagate = False
    target.setLevel(level)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    data: DataOption = None,
    settings: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            metavar="KEY=VALUE",
            help=(
                "Override a setting below config/chancellor for this run, e.g. "
                "--set wrap_width=80; repeatable. The value is plain YAML. It enters the "
                "configuration digest, so a later --check without it reports drift."
            ),
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Log the load steps to stderr.")
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """Chancellor: documents from the project data tree."""
    del version
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG, stream=sys.stderr, format="%(name)s: %(message)s"
        )
    overrides = parse_overrides(settings or [])
    if overrides:
        _show_on_stderr("chancellor.overrides", logging.INFO, "%(name)s: %(message)s")
    _show_on_stderr("chancellor.references", logging.WARNING, "warning: %(message)s")
    ctx.obj = {"data": data, "overrides": overrides}


def _data(ctx: typer.Context) -> Path | None:
    return (ctx.obj or {}).get("data")


def _load(ctx: typer.Context, *, require_data: bool = True) -> Project:
    """The project for a command, with the run's `--set` overrides applied."""
    return Project.load(
        _data(ctx),
        require_data=require_data,
        overrides=(ctx.obj or {}).get("overrides"),
    )


def _read_input(source: Path) -> Any:
    if str(source) == "-":
        return parse_yaml(sys.stdin.read(), "stdin")
    try:
        text = source.read_text("utf-8")
    except OSError as exc:
        raise ConfigError(f"{source}: {exc.strerror or exc}") from exc
    return parse_yaml(text, str(source))


@app.command("render", epilog=EPILOG)
def render_command(
    ctx: typer.Context,
    kind: Annotated[
        str,
        typer.Argument(
            help="Kind or alias: decisions (adr), requirements (arr), specifications (asr), "
            "adr-core, arr-core, asr-core, or a provider's kind."
        ),
    ],
    source: Annotated[
        Path,
        typer.Argument(
            metavar="INPUT", help="YAML mapping with the record; '-' reads stdin."
        ),
    ],
) -> None:
    """Validate one record and print its document to stdout; nothing is written.

    Without a data file the built-in defaults apply. A core document's index is generated
    from the project's records of that kind, if a project is found.

    Exit codes: 0 success, 1 configuration error, 2 invalid input, 6 internal error.
    """
    project = _load(ctx, require_data=False)
    spec, part = project.registry.lookup(kind)
    model = spec.model_for(part)
    raw = model.model_load(_read_input(source))
    try:
        record = model.model_validate(raw)
    except ValidationError as exc:
        raise InputError.from_validation(exc, model) from exc
    if part == "core_document":
        section = project.sections.get(spec.name)
        record = record.index_records(  # type: ignore[attr-defined]
            section.records if section else [],
            suffix=template_suffix(spec.templates.records),
        )
    typer.echo(
        render_document(
            record,
            spec.template(part),
            registry=project.registry,
            formatter=project.formatter(),
            context=project.format_context(),
            data_hash=data_hash(record),
            refs=project.ref_context(record),
            extras=project.template_extras(record),
        ),
        nl=False,
    )


@app.command(epilog=EPILOG)
def schema(
    ctx: typer.Context,
    name: Annotated[
        str,
        typer.Argument(
            help="A kind or alias, or: config (merged configuration), data (the record "
            "sections), provider (a provider manifest), lock (the lock file)."
        ),
    ],
) -> None:
    """Print a JSON Schema, field descriptions included, for the resolved provider set.

    Exit codes: 0 success, 1 configuration error or unknown name, 6 internal error.
    """
    project = _load(ctx, require_data=False)
    if name == SchemaTarget.CONFIG:
        root = project.root_model.model if project.root_model else None
        base = config_class(root, project.keys)
        result = config_model(project.registry, base=base).model_json_schema()
    elif name == SchemaTarget.DATA:
        model = (
            project.root_model.model
            if project.root_model
            else project.registry.root_model()
        )
        result = model.model_json_schema()
    elif name == SchemaTarget.PROVIDER:
        result = ProviderManifest.model_json_schema(by_alias=True)
    elif name == SchemaTarget.LOCK:
        result = Lock.model_json_schema(by_alias=True)
    else:
        spec, part = project.registry.lookup(name)
        result = spec.model_for(part).model_json_schema()
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("hash", epilog=EPILOG)
def hash_command(
    ctx: typer.Context,
    ids: Annotated[
        list[str] | None, typer.Argument(help="Record IDs; default: all.")
    ] = None,
) -> None:
    """Print the data hash of records, as written into their documents.

    Exit codes: 0 success, 1 configuration error or unknown ID, 2 invalid input,
    6 internal error.
    """
    project = _load(ctx)
    wanted = [project.resolve_id(i) for i in ids] if ids else sorted(project.records)
    unknown = [i for i in wanted if i not in project.records]
    if unknown:
        raise ConfigError(f"Unknown record IDs: {', '.join(unknown)}")
    for record_id in wanted:
        typer.echo(f"{record_id}\t{data_hash(project.records[record_id][1])}")


@app.command(epilog=EPILOG)
def build(
    ctx: typer.Context,
    check: Annotated[
        bool,
        typer.Option("--check", help="Write nothing; exit 3 if anything would change."),
    ] = False,
    strict: Annotated[
        bool, typer.Option("--strict", help="Exit 4 if the build has degradations.")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="List only documents that change.")
    ] = False,
) -> None:
    """Render every document whose inputs changed since the lock, and update the lock.

    Each document is listed as new, changed, modified (edited on disk), unchanged, removed
    (orphan deleted), orphan (kept: edited on disk, or listed only by an unusable lock) or
    untracked (kept: named like a document of its folder, known to no record or lock; a
    warning, not drift).

    Exit codes: 0 success, 1 configuration error, 2 invalid input, 3 drift found by
    --check, 4 degradations under --strict, 6 internal error.
    """
    project = _load(ctx)
    result = run_build(project, check=check)
    for rel, status in result.statuses:
        if not (quiet and status == "unchanged"):
            typer.echo(f"{status}\t{rel}")
        if status == "untracked":
            typer.echo(
                f"warning: {rel} is named like a document but no record produces it; "
                "kept (chancellor only deletes files it wrote)",
                err=True,
            )
    if result.lock_changed:
        typer.echo(f"{'stale' if check else 'updated'}\t{project.config.lock}")
    for degradation in result.degradations:
        typer.echo(
            f"degradation: {degradation.code}: {degradation.subject}: {degradation.message}",
            err=True,
        )
    if check and result.drift:
        raise ResultCode(ExitCode.DRIFT)
    if strict and result.degradations:
        raise ResultCode(ExitCode.DEGRADED)


@app.command(epilog=EPILOG)
def providers(ctx: typer.Context) -> None:
    """List the loaded providers in load order: name, origin, type, fingerprint, kinds.

    Exit codes: 0 success, 1 configuration error, 2 invalid input, 6 internal error.
    """
    project = _load(ctx, require_data=False)
    fingerprints = project.registry.fingerprints()
    for provider in project.registry.providers:
        kinds = ", ".join(sorted(provider.manifest.kinds)) or "-"
        kind_of = "code" if provider.code else "declarative"
        typer.echo(
            f"{provider.name}\t{provider.origin}\t{kind_of}\t{fingerprints[provider.name]}\t{kinds}"
        )
    for kind, override in sorted(project.model_overrides.items()):
        typer.echo(
            f"model:{kind}\t{', '.join(override.origins)}\tcode\t{override.fingerprint}\t"
            f"{', '.join(override.references)}"
        )
    if project.root_model is not None:
        info = project.root_model
        typer.echo(
            f"data_model\t{info.origin}\tcode\t{info.fingerprint}\t{info.reference}"
        )


@app.command(epilog=EPILOG)
def explain(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(metavar="ID", help="Record ID.")],
) -> None:
    """Name the digest parts of a record's documents that moved since the lock.

    Parts: data, refs, files, templates, config, api, providers.

    Exit codes: 0 success, 1 configuration error or unknown ID, 2 invalid input,
    6 internal error.
    """
    project = _load(ctx)
    for line in explain_record(project, project.resolve_id(record_id)):
        typer.echo(line)


@app.command(epilog=EPILOG)
def doctor(ctx: typer.Context) -> None:
    """Check the project: declared providers, sections, wrap width, outputs, degradations.

    Exit codes: 0 no problems (notes may be printed), 1 configuration problems, 2 record data
    problems (such as one-sided links) and no configuration problems, 6 internal error.
    """
    report = diagnose(_data(ctx))
    for note in report.notes:
        typer.echo(f"note: {note}")
    for problem in [*report.problems, *report.input_problems]:
        typer.echo(f"problem: {problem}", err=True)
    if report.problems:
        raise ResultCode(ExitCode.CONFIG)
    if report.input_problems:
        raise ResultCode(ExitCode.INPUT)


@app.command(epilog=EPILOG)
def lint(
    ctx: typer.Context,
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Files to check; default: what the linter decides."),
    ] = None,
) -> None:
    """Run the configured linter (config/chancellor/linter).

    Exit codes: 0 no problems, 1 configuration error (including no linter set), 5 the linter
    reported problems, 6 internal error.
    """
    project = _load(ctx, require_data=False)
    ref = project.config.linter
    linter_type = project.type_class("linters", ref.type)
    try:
        linter = linter_type(**ref.arguments())
    except ValidationError as exc:
        raise ConfigError(f"Invalid arguments for linter {ref.type}: {exc}") from exc
    result = linter.lint(paths or [], LintContext(root=project.root))
    if result.output:
        typer.echo(result.output, nl=not result.output.endswith("\n"))
    if result.problems:
        raise ResultCode(ExitCode.LINT)


USAGE_EXIT = 2
"""Exit code the command-line parser uses for misuse; chancellor reports it as 1."""


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return its exit code; misuse maps to 1, surprises to 6.

    Commands raise `ChancellorError` for expected failures and `ResultCode` for findings, never
    `SystemExit` with a code, so the parser's `USAGE_EXIT` on misuse is unambiguous.
    """
    command = typer.main.get_command(app)
    try:
        command.main(args=argv, prog_name="chancellor", standalone_mode=True)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        return int(ExitCode.CONFIG) if code == USAGE_EXIT else code
    except ChancellorError as exc:
        if str(exc):
            typer.echo(f"error: {exc}", err=True)
        return int(exc.code)
    except Exception:  # pylint: disable=broad-exception-caught
        typer.echo("internal error:\n" + traceback.format_exc(), err=True)
        return int(ExitCode.INTERNAL)
    return int(ExitCode.SUCCESS)


def run() -> None:
    """Console-script entry point."""
    sys.exit(main())
