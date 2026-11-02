# Running the tests

```bash
poetry do test
```

The tests live in `tests/` and run with pytest.

## Both configurations

Chancellor must work with and without the `git` extra, so the tests run in both configurations. CI
runs every supported Python version twice, once with `--all-extras` and once without extras. To
reproduce the no-git configuration locally, install without extras:

```bash
poetry install
poetry do test
```

```{note}
The test suite for the renderer, including its fixtures, is documented with the source migration.
```
