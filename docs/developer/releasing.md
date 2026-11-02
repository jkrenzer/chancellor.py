# Releasing

Pushing a `v*` tag publishes the package to PyPI.

## How versions are made

Two tools share the work:

- [bump-my-version](https://callowayproject.github.io/bump-my-version/) decides release numbers. It
  writes the release version into `[tool.poetry] version` in `pyproject.toml` (and into any other
  file listed under `[[tool.bumpversion.files]]`), commits, and creates the annotated tag
  `v<version>`.
- [poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning) gives every
  build its version from git. On a tagged commit that is the tag's version, e.g. `0.1.0`. Between
  releases it is the next patch as a development release with the commit hash, e.g.
  `0.1.1.dev3+g9f2c1ab` three commits after `v0.1.0`.

This applies to every way chancellor is built: wheels and sdists, `poetry install` in a checkout,
and installs straight from the repository URL (`pip install git+https://…`). Archive downloads,
which carry no git history, take the version from `.git_archival.json`, which `git archive` fills
in. `chancellor.__version__` and `chancellor --version` read the installed package metadata.

An editable install (`poetry install`) records the version at install time; it does not change with
later commits until the next `poetry install`.

Poetry installs the plugin into `.poetry/` in the repository on the first `poetry install`.

## Procedure

1. Make sure `main` is green and checked out locally.

2. Bump the version. This updates `pyproject.toml`, commits the change as
   `chore(release): bump version …` through the pre-commit hooks, and creates the tag `v<version>`:

   ```bash
   poetry do release-patch   # or release-minor, release-major
   ```

3. Push the commit and the tag:

   ```bash
   git push origin main
   git push origin v<version>
   ```

4. The `release` workflow runs the full test matrix and checks that the tag equals the package
   version. Only then does it build the package and publish it to PyPI through Trusted Publishing. A
   tag pushed without `poetry do release-*`, or on a commit whose tests fail, publishes nothing.

## TestPyPI

Running the `release` workflow manually (workflow dispatch) builds the package from the selected
branch and publishes it to TestPyPI instead. This is a dry run of the build and of Trusted
Publishing. Package indexes reject the `+g<hash>` part, so the job publishes the version without it,
e.g. `0.1.1.dev3`. TestPyPI rejects a version that was already uploaded, so a second dispatch from
the same commit fails.

TestPyPI is a separate service with its own project names. A successful upload there says nothing
about whether the name is available on PyPI.

## First release

No release tag exists yet, so builds currently report `0.0.1.dev<n>+g<hash>`. `poetry do release-*`
bumps *past* the version in `pyproject.toml`, so the first release, `0.1.0`, is tagged by hand on
the release commit:

```bash
git tag -a v0.1.0 -m "chore(release): 0.1.0"
git push origin v0.1.0
```

From then on, use `poetry do release-*`.

## One-time setup

Trusted Publishing must be configured before the first upload to each index. For a project that does
not exist there yet, this is a *pending publisher*:

- on PyPI, for the project `chancellor`, the `release.yml` workflow of this repository and the
  `pypi` environment;
- on TestPyPI, for the same project and workflow and the `testpypi` environment.

Registering the pending publisher on PyPI also shows early whether the project name is available.
