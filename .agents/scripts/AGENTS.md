# scripts folder guide

Keep scripts minimal, auditable, and vendor-neutral.

## Index

- `README.md`: human-facing overview.
- `pyright_config.py`: points pyright at the project venv via the gitignored `pyrightconfig.json`;
  run as `poetry do pyright-config`, and before every `poetry do serena`.
- `savepoint.sh`: named save point of the whole working tree as a stash entry, without touching the
  working tree or the index; see `../context/coworking.md`.
- `usage-sample.sh`: records one Claude usage sample (5-hour and weekly window) from `caut` to
  `.agents/tmp/coworking/usage.ndjson` for pacing; see `../context/coworking.md`.
