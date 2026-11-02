"""Exit codes and the errors that map onto them.

The exit-code table is the one place a command's result code comes from (0.1.0:D0010). Every error
chancellor raises on purpose derives from `ChancellorError` and carries its code, so a script
calling chancellor can tell a misconfiguration from a finding.
"""

from enum import IntEnum

from pydantic import BaseModel, ValidationError


class ExitCode(IntEnum):
    """Result codes of every chancellor command; meanings in `EXIT_CODE_MEANINGS`."""

    SUCCESS = 0
    CONFIG = 1
    INPUT = 2
    DRIFT = 3
    DEGRADED = 4
    LINT = 5
    INTERNAL = 6


EXIT_CODE_MEANINGS: dict[ExitCode, str] = {
    ExitCode.SUCCESS: "Success",
    ExitCode.CONFIG: (
        "Configuration error, including `builtin.none` under `lint` and command-line misuse"
    ),
    ExitCode.INPUT: "Input invalid: duplicate IDs, dangling refs, a record failing its model",
    ExitCode.DRIFT: "`--check` found drift",
    ExitCode.DEGRADED: "`--strict` found degradations",
    ExitCode.LINT: "The linter reported problems",
    ExitCode.INTERNAL: "Internal error",
}
"""Meaning of each exit code. Enum members carry no docstrings at runtime, so the table lives
here, in the one place every help text reads it from."""

EXIT_CODE_HELP = "\n".join(
    f"{code.value}  {EXIT_CODE_MEANINGS[code]}" for code in ExitCode
)
"""The exit-code table as plain text, for command help."""


class ChancellorError(Exception):
    """An expected failure; `code` is the exit code it maps onto."""

    code: ExitCode = ExitCode.INTERNAL


class ResultCode(ChancellorError):
    """Ends a command with a code from the table, its output already written.

    Commands use it instead of `SystemExit`, so a `SystemExit` with the parser's usage code
    can only mean command-line misuse.
    """

    def __init__(self, code: ExitCode) -> None:
        super().__init__("")
        self.code = code


class ConfigError(ChancellorError):
    """The configuration, a provider or the command line is wrong."""

    code = ExitCode.CONFIG


class InputError(ChancellorError):
    """Record data is invalid."""

    code = ExitCode.INPUT

    @classmethod
    def from_validation(
        cls, error: ValidationError, model: type[BaseModel] | str, *, prefix: str = ""
    ) -> "InputError":
        """List every violation of a validation error, one per line."""
        name = model if isinstance(model, str) else model.__name__
        return cls("\n".join([f"Invalid {name} input:", *violations(error, prefix)]))


def violations(error: ValidationError, prefix: str = "") -> list[str]:
    """One `- location: message` line per violation of a validation error."""
    lines = []
    for detail in error.errors():
        location = location_text(detail["loc"], prefix)
        message = detail["msg"].removeprefix("Value error, ")
        lines.append(f"- {location}: {message}" if location else f"- {message}")
    return lines


def location_text(loc: tuple[int | str, ...], prefix: str = "") -> str:
    """Dotted location with list indexes in brackets, e.g. `decisions.records[2].title`."""
    text = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in loc)
    return (prefix + text).lstrip(".")
