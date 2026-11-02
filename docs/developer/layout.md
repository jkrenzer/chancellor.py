# Project layout

| Path                                | Content                                                   |
| ----------------------------------- | --------------------------------------------------------- |
| `src/chancellor/`                   | The package. `cli.py` holds the command-line entry point. |
| `src/chancellor/templates/builtin/` | Built-in Jinja2 templates, shipped in sdist and wheel.    |
| `tests/`                            | pytest test suite.                                        |
| `docs/`                             | This documentation: Sphinx with MyST Markdown sources.    |
| `arch/`                             | Chancellor's own architecture records.                    |
| `.github/workflows/`                | CI: tests, pre-commit hooks, and releases.                |
| `.agents/`                          | Rules, skills and context for AI coding agents.           |
| `pyproject.toml`                    | Package metadata and the configuration of all tools.      |

```{note}
The modules of the renderer are documented with the source migration.
```
