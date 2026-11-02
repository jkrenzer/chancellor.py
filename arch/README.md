# Architecture records

Chancellor's own architecture: the decisions taken, the requirements it must meet, and the
specifications that describe how it meets them. Chancellor exists to keep records like these as data
and render them into documents, so it manages its own records too.

| Path              | Content                                                         |
| ----------------- | --------------------------------------------------------------- |
| `data/`           | The records as data, one YAML file per kind. Edit these.        |
| `decisions/`      | Decision records: what was decided, why, and what was rejected. |
| `requirements/`   | Requirements chancellor must satisfy.                           |
| `specifications/` | Specifications of formats, interfaces and behaviour.            |
| `chancellor.lock` | What the last build saw; written by chancellor, do not edit.    |

The documents in the three record folders are rendered by chancellor from `data/`. `chancellor.yaml`
in the repository root names each kind's data file under `kinds.<kind>.data`. To change a record,
edit its data and run:

```bash
poetry run chancellor build
```

`poetry run chancellor build --check` reports drift without writing; `chancellor doctor` checks the
project.
