# Contributing

## Commit messages

This repository enforces Conventional Commits (`conventional-pre-commit --strict`). Use these types:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `build`
- `ci`
- `chore`

Recommended scopes in this repository include:

- `packaging`
- `deps`
- `cli`
- `templates`
- `tests`
- `docs`
- `ci`
- `agents`
- `cla`

## Branch naming

Use:

```text
<user>-<yyyy-mm-dd>-<topic>-v<nn>
```

Example:

```text
jkrenzer-2026-10-27-bootstrap-repo-v01
```

## Pull requests

- Keep PRs focused and small.
- Ensure `poetry do lint` and `poetry do test` pass.
- For releases, configure Trusted Publishing on PyPI before pushing the first `v*` tag.

## Licensing of contributions

Chancellor is licensed under the GNU Affero General Public License, version 3 only
(`AGPL-3.0-only`). Jörn Krenzer is named as proxy under its section 14 and decides whether later
versions of the AGPL may be used.

Before a contribution can be merged, its author must accept the contributor licence agreement:

- individuals: [`CLA.md`](CLA.md);
- employers and other legal entities: [`CLA-entity.md`](CLA-entity.md), when contributions are made
  as part of someone's work.

The agreement grants everyone the right to use contributions under the project licence. It also lets
the maintainer designate further free software licences, should a licence formality ever stand in
the way of a legitimate free software use, such as using Chancellor as a module in another free
project. Only licences the Free Software Foundation recognises as free can be designated, and only
for everyone alike. Chancellor can never be offered under a proprietary licence. You keep your
copyright.

To accept, run `poetry do sign-cla` and add the record it writes to your pull request. This is
needed once. The `cla` check fails until every commit author and co-author is covered. See
[`cla/README.md`](cla/README.md) for details and for signing without the helper.
