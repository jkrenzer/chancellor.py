# Agent instructions

This repository is maintained with multiple AI coding tools. `AGENTS.md` is the single source of
truth; vendor-specific files should only point here.

## Repository index

- `.agents/`: vendor-neutral agent assets; see `.agents/AGENTS.md`.
- `.claude/`: tool-prescribed. `agents` and `skills` are git symbolic links into `.agents/`.
- `.devcontainer/`: tool-prescribed. Dev container built from the `agent` stage of the root
  `Dockerfile`, for local use and Codespaces. Project settings in `config.env`; tie-in points for
  new environments, agent CLIs and MCP servers at the top of `lib.sh`. See
  `docs/developer/environments.md`.
- `.github/`: tool-prescribed. CI workflows and the Copilot pointer file.
- `.vscode/`: tool-prescribed. Recommended editor extensions; `mcp.json` registers the GitHub MCP
  server for VS Code.
- `arch/`: chancellor's own architecture records (decisions, requirements, specifications), managed
  with chancellor itself; see `arch/AGENTS.md`.
- `cla/`: contributor licence agreement records, signing helper and CI check; see `cla/AGENTS.md`.
  The agreements themselves are `CLA.md` and `CLA-entity.md`.
- `docs/`: user and developer documentation, Sphinx with MyST Markdown sources.
- `src/chancellor/`: the package; built-in providers (manifests, models, templates) in `builtin/`.
- `tests/`: pytest test suite.
- `tmp/`: gitignored. Temporary files that are not agent context: generated code, downloads, build
  or test artefacts. Use a subfolder per task.
- `.mcp.json`: registers the `chancellor-records` MCP server. It only works once the source
  migration has landed; until then `chancellor serve` does not exist.
- `.git_archival.json`: `git archive` fills in its `$Format:` placeholders so archive downloads know
  their version (see `docs/developer/releasing.md`). Leave the placeholders as they are.
- `.poetry/`: gitignored. Poetry installs the poetry-dynamic-versioning plugin here.
- `CLAUDE.md`, `.github/copilot-instructions.md`: thin pointers to this file.

## Context persistence rules

- At the start of a session, look for persisted context below `.agents/`, including `.agents/tmp/`:
  hand-off documents, work-state records, work boards, plans and notes.
  - Tell the user briefly which context you found and picked up.
  - If something is obviously missing — a hand-off refers to a file that does not exist, or a record
    stops mid-task — ask the user about it.
- While you work, persist relevant context, plans and progress, so another agent or session can pick
  up where you left off. Always record where things live.
  - Session-bound context — hand-offs, work boards, plans, notes — goes below `.agents/tmp/`. It is
    gitignored and stays on this machine. Other temporary files go below `tmp/` (see the index).
  - Context that shapes the work of future agents or sessions is preserved in git, in the fitting
    subfolder of `.agents/` (usually `.agents/context/`).
  - Judge carefully what is important and long-lived enough for git history. Before preserving
    anything in git, give the user an overview and ask for approval.
- **Never** preserve credentials, personal information about users, or other sensitive material in
  git history.
  - Record instead how another agent can reacquire it, e.g. by asking the user to log in or to
    provide a token.
  - The *only* exception is material encrypted with a credible encryption tool, where only the
    ciphertext is committed to git or stored in Git LFS.

## Working alongside other sessions

Several agent sessions may work in this tree at the same time. Reduce the risk of collisions:

- Put your temporary files in a subfolder named after your task, e.g. `.agents/tmp/<task>/` and
  `tmp/<task>/`, not loose in the shared folder.
- In documents several sessions edit, add your content as its own section or entry instead of
  rewriting what others wrote.
- Re-read a file right before you change it, and keep edits small and targeted rather than rewriting
  whole files.
- Do not run commands that write across the whole tree (`poe format`, `poe prek`, formatters on `.`)
  while other sessions are active. Limit them to the files you changed, e.g.
  `pre-commit run --files <paths>`.
- Files that appear or change without your doing belong to someone else: do not revert, move or
  reformat them. Tell the user instead.

## Folder documentation rules

- A folder with a purpose of its own includes a `README.md` and an `AGENTS.md`.
- A folder whose purpose is customary (`src/`, `tests/`, `docs/`) gets only a short description in
  its parent's index.
- A folder whose layout a tool prescribes gets no `README.md` or `AGENTS.md` of its own; its parent
  describes it instead. The tool may read every file in it — Markdown files in `.agents/agents/` are
  loaded as subagent definitions.
- A folder's `AGENTS.md` indexes the folder and states folder-specific rules.
- Use progressive context loading: read parent instructions first, then descend.
- A child rule can override a parent rule only when it names the overridden rule and explains why
  the override is required.

## Git and commit rules

- Never commit, push, rebase, or create branches unless explicitly requested.
- Propose commits only after requested work is complete and verified.
- Use Conventional Commits and validate with `conventional-pre-commit --strict`.

## Markdown rules

- Keep lines at 100 characters unless a longer line is unavoidable.
- Use consistent heading levels and fenced code blocks with language hints.

## Tooling notes

- Use the GitHub MCP server or the `gh` CLI to read issues, pull requests and other GitHub
  information that touches or is touched by your work.
- Use Poetry for dependency management and virtual environments.
- Use `poe` tasks for routine formatting, linting, testing, docs, and release actions.
- Run pre-commit hooks before proposing commits.
