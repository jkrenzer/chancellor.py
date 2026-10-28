# Development setup

Chancellor uses [Poetry](https://python-poetry.org/) 2.3 or later for dependencies and virtual
environments, and [Poe the Poet](https://poethepoet.natn.io/) tasks for routine work.

## Local setup

```bash
git clone https://github.com/jkrenzer/chancellor.py.git
cd chancellor.py
poetry install --all-extras
poetry run pre-commit install
```

`poetry install` installs the `dev` and `docs` dependency groups. `--all-extras` adds the `git`
extra; leave it out to work in the no-git configuration.

## Routine tasks

| Task                     | Purpose                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| `poetry run poe format`  | Format Python and Markdown files.                                 |
| `poetry run poe lint`    | Check formatting, run pylint, and lint Markdown.                  |
| `poetry run poe test`    | Run the test suite.                                               |
| `poetry run poe docs`    | Build this documentation as HTML into `docs/_build/html`.         |
| `poetry run poe docs-md` | Build this documentation as Markdown into `docs/_build/markdown`. |
| `poetry run poe prek`    | Run all pre-commit hooks on the whole tree.                       |
