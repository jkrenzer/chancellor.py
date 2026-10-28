# Installation

This page covers installing chancellor and choosing between the configurations with and without git
support.

## Requirements

Chancellor requires Python 3.11 or later.

## Installing the package

```bash
pip install chancellor
```

```{note}
The package is not yet published on PyPI. The first release follows the source migration.
```

## The `git` extra

Chancellor runs without git. Git support is optional and installed through the `git` extra, which
adds [dulwich](https://www.dulwich.io/), a pure-Python git implementation:

```bash
pip install 'chancellor[git]'
```

Without the extra, chancellor runs in its no-git configuration. This is a supported, tested
configuration, not a degraded mode: chancellor never uses git to resolve paths. Git is consulted
only to answer two questions about a file, whether it is tracked and whether it is ignored.

```{note}
What chancellor reports in place of these answers when git is unavailable is documented with the
source migration.
```
