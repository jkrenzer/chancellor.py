"""Built-in linter types. `builtin.none` is the default."""

from collections.abc import Sequence
from pathlib import Path

from .api import LintContext, Linter, LintResult
from .errors import ConfigError


class NoneLinter(Linter):
    """No linter configured: `lint` fails with a configuration error, not a lint finding."""

    def lint(self, paths: Sequence[Path], context: LintContext) -> LintResult:
        del paths, context
        raise ConfigError(
            "No linter set; configure config/chancellor/linter with a linter type"
        )
