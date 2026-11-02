# Safety: consent and secrets

## Consent for git

- Never run `git add`, `git commit`, `git push`, `git stash`, `git rebase` or branch changes without
  the user's explicit consent to that step. "Set it up" is not consent to commit.
- Before asking: show `git status --short` and the exact files and a proposed Conventional Commits
  message. After a yes, stage exactly those paths (`git add -- <paths>`), never `-A` or `.`; other
  sessions may have files in the tree.
- A push needs its own consent, naming the remote and branch.

## Keep secrets out

Add to `.gitignore` before anything else is written (merge, do not replace):

```gitignore
# Local SSH files for the dev container; only the README is tracked.
.ssh/*
!.ssh/README.md
# Local environment files
.env
.env.*
!.env.example
```

Watch for check-ignore patterns that hide wanted files: Python's standard `.gitignore` ignores
`env/` and `ENV/` (hence the hook folder is named `environments/`).

Places secrets leak from in this setup:

- `devcontainer.json` (`containerEnv`, `remoteEnv`, `runArgs`): only names and `${...}` references,
  never values.
- `config.env`: settings only; it is committed.
- `.ssh/`: public keys only, and the folder is gitignored anyway. A private key there is an incident
  even if ignored: tell the user.
- Logs and diagnostics: mask tokens (`gho_…`), never `set -x` around them.
- Commit messages and docs: no tokens, no real key material, no personal data beyond what the user
  agreed to (e.g. their git author name).

## Scan before proposing a commit

1. `git status --short` and `git diff --cached --stat` (if staged by the user).

2. If gitleaks is installed: `gitleaks dir <paths>` for the changed files; for staged changes
   `gitleaks protect --staged` (deprecated since v8.19 but working; check `gitleaks --help`).

3. Otherwise grep the changed files for key shapes:

   ```bash
   rg -n --hidden -e 'BEGIN [A-Z ]*PRIVATE KEY' -e 'gh[pousr]_[A-Za-z0-9]{20,}' \
     -e 'sk-(ant-)?[A-Za-z0-9_-]{20,}' -e 'AKIA[0-9A-Z]{16}' <paths>
   ```

4. Suggest a gitleaks pre-commit hook and GitHub push protection to the user; add the hook only on
   their yes.

## If something is found

Stop. Do not stage, commit or push. Tell the user the file, line and kind of secret (masked). Fix
together: remove or move it to an ignored file or a secret store, add the ignore rule, and if it
ever reached a commit or a remote, tell the user it must be rotated; rewriting history is their
decision. Proceed with publishing it only on the user's explicit order after you told them exactly
what would be published.

Sources: `links.md`, section "Secrets".
