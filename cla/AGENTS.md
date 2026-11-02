# cla folder guide

Records of accepted contributor licence agreements, plus the helper and CI check for them. See
`README.md` for the record formats.

## Rules

- Never create, edit or delete a record in `signatures/` or `entities/` on anyone's behalf. A record
  is a legal declaration by its owner; only the owner, or for entities the maintainer after
  receiving the signed agreement, adds it.
- Never put an email address or any other contact data into a record. Signed entity agreements stay
  off-repo.
- `sign.py` and `check.py` use the Python standard library only. `check.py` must stay safe to run on
  untrusted pull requests: it reads pull request content as data and never executes it.
- A change to `CLA.md` or `CLA-entity.md` needs a new version and a new `cla-v<version>` tag; ask
  the maintainer first.
