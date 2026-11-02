"""Points pyright at the project's virtual environment.

Serena starts pyright through uvx, in an environment of its own, where pyright cannot see the
project's dependencies. This writes `venvPath` and `venv` for the interpreter running it into the
gitignored `pyrightconfig.json` at the repository root, keeps any other settings in that file, and
leaves the file untouched when it already points there. Run it through Poetry
(`poetry do pyright-config`) so that the interpreter is the project's.
"""

import json
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / "pyrightconfig.json"


def main() -> int:
    venv = Path(sys.prefix)
    if venv == Path(sys.base_prefix):
        print(
            f"pyright-config: {sys.executable} is not in a virtual environment",
            file=sys.stderr,
        )
        return 1
    config = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    wanted = {"venvPath": str(venv.parent), "venv": venv.name}
    if all(config.get(key) == value for key, value in wanted.items()):
        return 0
    config.update(wanted)
    CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    # stderr: the serena task runs this before an MCP server whose stdout is the protocol.
    print(f"pyright-config: {CONFIG.name} points at {venv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
