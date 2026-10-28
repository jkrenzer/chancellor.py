"""Sphinx configuration for the chancellor documentation."""

# Sphinx reads its settings from lowercase module-level names.
# pylint: disable=invalid-name

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# pylint: disable-next=wrong-import-position
from chancellor import __version__  # noqa: E402

project = "chancellor"
author = "Jörn Krenzer"
copyright = "2026, Jörn Krenzer"  # pylint: disable=redefined-builtin
release = __version__

extensions = ["myst_parser"]

exclude_patterns = ["_build"]
source_suffix = {".md": "markdown"}

html_theme = "alabaster"
