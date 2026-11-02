"""Chancellor package."""

from importlib.metadata import version

# Set at build time from git by poetry-dynamic-versioning, e.g. 0.1.1.dev3+g9f2c1ab.
__version__ = version("chancellor")
