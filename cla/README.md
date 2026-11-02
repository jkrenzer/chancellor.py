# Contributor licence agreement records

This folder holds the acceptance records for the contributor licence agreements in the repository
root, [`CLA.md`](../CLA.md) for individuals and [`CLA-entity.md`](../CLA-entity.md) for employers
and other legal entities, and the tooling around them.

## Signing as an individual

Run this in the repository and confirm the record it shows:

```bash
poetry do sign-cla
```

The helper takes your name from `git config user.name` and your GitHub login and id from the GitHub
CLI (`gh`). Without `gh` it asks for your login. It needs only Python, so `python3 cla/sign.py`
works outside the virtual environment too.

Commit the new file and include it in your pull request, opened from your own account. You do this
once; later pull requests are covered.

Without the helper, create `signatures/<github-login>.md` (login in lower case) by hand:

```markdown
---
name: "Alice Example"
github-login: alice
github-id: 123456
agreement: CLA.md
version: "1.0"
date: 2026-11-02
---

I, Alice Example, have read the Chancellor Individual Contributor Licence Agreement, version 1.0
(git tag cla-v1.0), and accept it for all my Contributions to Chancellor.
```

Your numeric id is shown at `https://api.github.com/users/<github-login>`.

## Signing for an entity

The entity signs `CLA-entity.md` and emails the PDF to the maintainer. The maintainer then adds
`entities/<entity-slug>.md`:

```markdown
---
entity: "Example GmbH"
agreement: CLA-entity.md
version: "1.0"
date: 2026-11-02
github-ids: [123456, 234567]
---

Authorised Contributors: alice (123456), bob (234567).
```

## Co-authors

`Co-authored-by:` trailers are checked as well. Write them with the co-author's GitHub `noreply`
address, `<id>+<login>@users.noreply.github.com`, so the check can identify them.

## Contents

- `signatures/`: one record per individual who accepted `CLA.md`.
- `entities/`: one record per entity that signed `CLA-entity.md`.
- `sign.py`: helper that writes an individual record, run by `poetry do sign-cla`.
- `check.py`: the check run by `.github/workflows/cla.yml` on every pull request.
