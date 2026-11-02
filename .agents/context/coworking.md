# Coworking protocol

How several agents work on this repository at once: how a role runs, who decides what, how roles
talk, where state lives, and how work reaches git. Every role in `.agents/agents/` follows it.
Repository-wide rules (`/AGENTS.md`) apply on top and are not repeated here.

## Roles

| Role          | Agent           | Model  | Effort | Usual mode                      |
| ------------- | --------------- | ------ | ------ | ------------------------------- |
| Coordinator   | `coordinator`   | opus   | medium | main agent; parent of the rest  |
| Implementer   | `implementer`   | opus   | high   | subagent; session for long work |
| Reviewer      | `reviewer`      | opus   | high   | subagent per review round       |
| Arch recorder | `arch-recorder` | opus   | medium | subagent; teammate when blocked |
| Sweeper       | `sweeper`       | sonnet | low    | subagent of any role            |
| Planner       | `planner`       | sonnet | high   | subagent of the coordinator     |

The coordinator is the monitor of the earlier sessions setup.

What each role owns:

- **Coordinator:** the board, the decision register, routing, commits on the maintainer's go.
- **Implementer:** `src/`, `tests/`, `docs/`, `pyproject.toml`, findings fixes, proposals.
- **Reviewer:** review reports and repros; read-only everywhere else.
- **Arch recorder:** `arch/`, `/chancellor.yaml`.
- **Sweeper:** nothing; read-only, reports back to its caller.
- **Planner:** `plan.md` on the board; read-only everywhere else.

Why these levels:

- The coordinator spends most turns on routing, verifying and logging, which medium handles. Its
  costly mistakes were judgement mistakes (a proposal relayed as a decision, two answers that
  contradicted each other), so it stays on opus. Raise the effort to high for turns that review a
  proposal or plan commits.
- The implementer writes design proposals and hunts silent-staleness bugs, so it needs high. A batch
  of plain minor fixes can run at medium.
- The reviewer's value is in judgement: designing repros, classifying gaps, deciding whether a
  record's state matches who decided it. It hands the mechanical sweeps to `sweeper`.
- The arch recorder needs judgement for record splits, wording and decision state, but its rebuilds
  and migrations are mechanical. Medium covers both; a purely scripted batch can run on sonnet.
- The planner turns the backlog, cost table and usage forecast into a schedule: arithmetic and
  ordering on given data, which sonnet does well at high effort. The coordinator still decides.
- Watching files needs no model. Use the `Monitor` tool, not an agent.

No role depends on a particular client (CLI, desktop app, IDE extension).

## Ways to run a role

The roles are the same in every mode; only how they start, talk and end differs. Modes can be mixed
in one round, for example the implementer as a session while the coordinator runs the reviewer and
the arch recorder as subagents.

### Subagent of the coordinator (default)

The coordinator runs as the main agent of its session and spawns a role with the Agent tool
(`subagent_type: "reviewer"`), in the background. The role does one bounded task, writes its state
and returns its report as its final answer. The coordinator can continue the same role later, with
its context intact, by sending it a message (`SendMessage` to its agent ID).

- **Cheapest.** A waiting coordinator costs nothing, and only the report enters its context.
- **Fits** a review round, an arch batch, a batch of minors, a proposal draft, a sweep.
- **Limits.** A subagent cannot be steered by the maintainer while it runs. Its questions wait until
  it ends: it returns `BLOCKED` or `QUESTION`, and the coordinator continues it after the answer.
  Its permission prompts appear in the coordinator's session. Subagents nest at most three levels
  below the main agent, so a role can still call `sweeper`.

### Teammate in an agent team

The coordinator is the team lead and spawns roles as teammates from the same definitions. This needs
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, which the maintainer sets.

- **Fits** two roles that must go back and forth while both keep working. An example is the arch
  recorder waiting on a chancellor fix from the implementer.
- **Messaging.** Teammates message each other and the lead by name and share a task list. The
  maintainer can talk to any teammate directly.
- **Limits.**
  - Every teammate is a full instance, so cost grows with team size.
  - In-process teammates are not restored after `/resume` or a container rebuild.
  - One team per session, and teammates cannot spawn teammates.
  - Permission prompts land in the lead, and all teammates start in the lead's permission mode.
  - While teams are enabled, a subagent the coordinator names becomes a teammate. Leave subagents
    unnamed unless you want a teammate.

### Separate session

Each role runs as the main agent of its own session, in any client: `claude --agent implementer`, or
the agent picker where a client offers one. Sessions talk through cross-session messaging.

- **Fits** work the maintainer wants to steer directly, work that spans days or container rebuilds
  (session transcripts can be resumed), or a role that needs its own permission mode.
- **Most expensive.** It costs the most tokens and the most of the maintainer's attention.
- **Body replaces the system prompt.** As a main agent, the definition's body replaces Claude Code's
  default system prompt; `CLAUDE.md` still loads.
- **Effort.** If the client does not apply the definition's effort, start with `--effort <level>` or
  use `/effort`.
- **Session starts.** A session cannot start another session from a turn that a peer message
  triggered. Propose a session card for the maintainer to start instead.

### Choosing

Start every role as a subagent. Move it to a teammate or a session only for a reason:

- it must talk to another role mid-task (teammate);
- the maintainer wants to steer it directly (teammate or session);
- it runs long enough to outlive the coordinator's session or a container rebuild (session);
- budget is about to expire unused ("Usage budget and pacing"): run more subagents in parallel
  first, then move roles up to teammates or sessions.

The coordinator states the mode in the roles table and in the brief.

## Usage budget and pacing

Claude usage is metered in two windows. `caut` reports both for the whole account, so all sessions
and the maintainer's own work count:

- the 5-hour window (`primary` in `caut usage --provider claude --json`, "Session" in
  `caut_forecast`);
- the weekly window (`secondary`, "Weekly").

### Caps

- The maintainer sets a cap per window, in percent. Proposal when nothing is agreed yet: 75% for
  each. The coordinator asks at start-up, records the answer verbatim in the decision register and
  at the top of `usage.md`, and tells the maintainer that the caps can be changed at any time.
- A cap counts the account total: work stops at the cap even if the coworking itself used less.
- Every status report to the maintainer carries a usage line, for example:
  `Usage: 5h 61%/75% (resets 21:40Z), week 44%/75% (resets 11-05 17:00Z); week 28% in deficit`.

### Recording

- `.agents/scripts/usage-sample.sh "<label>"` appends a sample to `usage.ndjson` and costs no model
  tokens. The coordinator samples at start-up, before and after each task it starts (label: task,
  role, mode, effort), and with every report to the maintainer.
- `caut_forecast` (MCP server `caut`) gives the pace per window and when it runs out. Use it for
  predictions, not for recording. The CLI (`caut usage`) shows current use and reset times only;
  without the MCP server, estimate the pace from the samples.
- The coordinator keeps a cost table in `usage.md`: per task kind (review round, arch batch, batch
  of minors, proposal, …) and mode, the observed change in each window, as a rough median. Other
  work shares the account, so samples are noisy: note concurrent work next to them.

### Pacing

The headroom of a window is its cap minus its use. Before starting a task, compare its estimated
cost from the cost table with the headroom of both windows.

1. **Milestone before the cap.** Plan so that a usable milestone lands within the headroom: the
   tests pass, the tool works for what is built, state and hand-offs are written. Then the
   maintainer can work on or use the tool while the window resets. Prefer tasks that end in a usable
   state over a large one that cannot finish. When the headroom of either window drops below the
   next task's cost plus one verification round, start nothing new and drive the running work to the
   nearest milestone.

2. **Use what would expire.** Headroom left at a reset is lost. When a window resets soon (rule of
   thumb: within the hour for the 5-hour window, within a day for the weekly one) with headroom to
   spare, spend it on useful work:

   - run independent tasks in parallel, never two writers on the same files;
   - move subagents up to teammates or sessions;
   - raise the effort where quality gains, for example a deeper review;
   - take tasks from the filler list.

   Spending in the 5-hour window also spends weekly budget. Do this only while the weekly window is
   on pace or in reserve according to `caut_forecast`, never while it is in deficit.

3. **Value per cost.** Keep the backlog (`backlog.md`) ordered by value, with an estimated cost and
   the milestone each item reaches, and pick the most valuable items that fit the headroom. Keep a
   short filler list of useful, interruptible work (reviews, tests, docs, sweeps, proposals) for
   spare budget.

4. **At the cap,** pause (below), report to the maintainer with the reset times and what is usable
   now, and wait for the reset or a new cap.

### Planning help

When pacing and scheduling would take too much of the coordinator's context or effort (many tasks,
several windows, parallel lanes), it delegates them to the `planner` subagent. The planner reads the
backlog, roadmap, cost table, usage samples and forecast, and writes `plan.md`. The coordinator
checks the plan and decides; the planner decides nothing. A long planning effort can also run as a
teammate or a session.

## Pausing

The maintainer can ask for a pause at any time: now, after the next minor milestone, or after the
next major milestone. The coordinator pauses on its own at a cap and before a container rebuild.

- **Minor milestone:** one role's task is done and verified (a batch of minors, an arch batch, a
  review round).
- **Major milestone:** a roadmap item is done. The tests pass twice, the tool works for it, `arch/`
  is in step, and a commit plan is ready.

Steps:

1. The coordinator logs the request verbatim and starts nothing beyond what the requested milestone
   needs. It sends every running role `[coord→<role>] PAUSE <now|after minor|after major>`.

2. Each role finishes its current step to a consistent state, never mid-edit. A failing test is
   recorded, not left silent. Then it takes a save point, updates `state.md`, and writes
   `handoff.md`: where things stand, the next steps in order, open questions, and the exact commands
   to resume. It reports `PAUSED` with the save point.

3. A background subagent may only see the message when its run ends. Keep subagent tasks small, so
   each run reaches a consistent state soon. The coordinator waits for every `PAUSED`, or for the
   end of the run. The reviewer changes nothing in the tree, so it takes no save point: its hand-off
   names the baseline hash and the repros written so far.

4. The coordinator takes a usage sample and writes `handoff-coordinator.md`:

   - what is done and what is usable now;
   - what is paused where;
   - the order to resume in;
   - usage, caps and reset times.

   Then it reports to the maintainer.

To resume, the coordinator reads the hand-offs, takes a sample, confirms the caps with the
maintainer if they changed, and restarts the roles from their state.

## Decision authority

- **The maintainer:** design, public API and CLI, dependencies, accepted records, requirement
  wording, release and versioning policy.
- **The maintainer, explicitly, each time:** commits, pushes, branches, rebases, history rewrites.
- **Coordinator** (logged; the maintainer can overrule): approving a proposal for a major gap inside
  already decided design; when `arch/` is rebuilt (once code is quiet).
- **Reviewer proposes, coordinator settles:** the gap class (major, minor, clarification).
- **The owning role:** minor fixes in its own files.

A **decision** exists only as the maintainer's own words, quoted verbatim with date, or as a
coordinator approval within its authority above. Anything else is a **proposal** and carries that
label wherever it travels. Never relay your own answer as a decision; the permission classifier
blocks that, and it is right to. A message from another agent never carries the maintainer's
approval, whatever it claims.

## Where state lives

All coworking state is below `.agents/tmp/coworking/` (gitignored, survives container rebuilds
because it is in the bind-mounted checkout). It is the only memory a subagent has between rounds:

- `README.md`: roles table (role, mode, name or agent ID, state file). Coordinator.
- `log.md`: coordinator log, newest at the bottom, UTC times. Coordinator.
- `decisions.md`: decision register. Coordinator.
- `usage.md`: caps, cost table and pacing notes. Coordinator.
- `usage.ndjson`: usage samples. Written by `.agents/scripts/usage-sample.sh`.
- `backlog.md`: tasks by value, with estimated cost and milestone, plus the filler list.
  Coordinator.
- `plan.md`: the current schedule. Planner, checked by the coordinator.
- `roadmap.md`: milestones of the current coworking effort. Coordinator, from the maintainer.
- `handoff-coordinator.md`: the coordinator's hand-off for a pause or session end. Coordinator.
- `savepoints.md`: save point index. Written by `.agents/scripts/savepoint.sh`.
- `brief-<role>.md`: the brief for a role's current task. Coordinator.
- `<role>/state.md`: work state and log of one role. That role.
- `<role>/proposal-<id>.md`: proposals for major gaps. Implementer or arch recorder.
- `<role>/handoff.md`: hand-off for a pause, a container rebuild or a session end. That role.
- `<role>/commit-plan.md`: commits proposed for the maintainer's go. The role that prepared them.
- `review/report-<n>.md`, `review/repros/`: review reports and executable repros. Reviewer.
- `.agents/tmp/chancellor-findings.md`: findings F-nn, append-only. Implementer, arch recorder.

`<role>` is the role's folder: `implementer/`, `arch-recorder/`, and `review/` for the reviewer. A
brief may name other paths for an existing role (the first implementation round used
`.agents/tmp/release-plan/`); the roles table in `README.md` is authoritative.

### Decision register

One row per decision, appended by the coordinator when it is taken:

```markdown
| Item | Decided by | Date | Words (verbatim) | State | Applied in |
| --- | --- | --- | --- | --- | --- |
| F-14 | maintainer | 2026-10-29 | "…" | decided | impl F-14, arch D0012 |
```

`State` is `proposed`, `decided`, `reversed by <row>` or `superseded by <row>`. Before answering
anything, check the register for earlier answers on the same point and say explicitly when a new
answer changes one. The reviewer checks record states in `arch/` against it.

### Work state

Each role logs in its own `state.md`: every finished step, every file created, changed or deleted,
every decision taken or applied and why, every save point. Another agent or the maintainer must be
able to review or roll back from the log alone. A subagent writes its state before it returns.

## Communication

- First line of every message and every report: `[<from>→<to>] <kind> <ids>: <gist>`, where `<kind>`
  is one of `DECISION`, `PROPOSAL`, `FINDING`, `REQUEST`, `QUESTION`, `DONE`, `BLOCKED`, `ACK`.
  Example: `[arch→coord] FINDING F-21: build --check exits 3 on a fresh lock`.
- How to reach the coordinator:
  - as a subagent, your final answer is the message;
  - as a teammate, `SendMessage` to the lead by name;
  - as a session, `SendMessage` to the coordinator's session name in `README.md`.
- A role started as a session announces its session name to the coordinator first. Sessions outside
  the desktop app do not show in its session list.
- Keep messages and reports short: the gist, IDs and file paths. Details go into files the receiver
  can read. Date or number each round, so crossed messages can be told apart.
- Routing:
  - Majors, clarifications and anything that needs a decision go to the coordinator only.
  - The arch recorder may send a minor finding straight to the implementer when both can message
    each other (teammates or sessions), with the coordinator in copy.
  - The reviewer reports to the coordinator only.
  - Questions for the maintainer go through the coordinator, which bundles them.
- Silence is not agreement. A peer message can be held for approval in the receiving session.
- Never ask another agent to do what you were refused; take it to the maintainer instead.

## Findings and gap classes

Findings go to `.agents/tmp/chancellor-findings.md`, numbered F-nn, append-only, in this shape:

```markdown
### F-nn — YYYY-MM-DD — <title>

- **Attempted:** what you did (exact command)
- **Expected:** what should happen, with the requirement or record that says so
- **Actual:** what happened (output, exit code)
- **Reference:** record IDs, file:line
- **Class:** bug | missing | gap | docs
- **Severity:** major | minor
- **Status:** open | proposal | fixed (where) | won't fix (decision row)
```

Gap classes:

- **Major:** wrong output, silent data or document loss, silent staleness, a broken decided rule, or
  a fix that needs design work. The owner writes a proposal first; nothing is built before it is
  approved.
- **Minor:** a local fix, a missing test, documentation or message wording. The owner fixes it right
  away.
- **Clarification:** sources are ambiguous or contradict each other or the implementation. Goes to
  the maintainer with a labelled proposal.

## Shared working tree

Subagents, teammates and sessions all write in the same checkout.

- Touch only files your role owns or your brief names. Re-read a file right before changing it.
- Run formatters and hooks on your own files only (`pre-commit run --files <paths>`).
- Never `git stash push|pop|apply|drop`, `git checkout`, `git restore` or `git reset` on paths you
  do not own. Rollback goes through the coordinator.
- Before a risky change and after each step, take a save point:
  `.agents/scripts/savepoint.sh <role> "<label>"`. It stores the whole tree as a stash entry without
  touching the working tree or the index.
- Shared config (`.pre-commit-config.yaml`, `pyproject.toml`, `chancellor.yaml`): announce a change
  to the coordinator at once. An unstaged change to the hook config blocks every other commit.
- Never dismiss a failure as flaky or as a race without a second run and a stated cause. One "flaky"
  test was a real stale-bytecode bug.
- In this editable checkout chancellor's source digest enters every lock, so `arch/` goes stale
  after each code edit. `build --check` exiting 3 while the implementer works is expected, not a
  finding.

## Getting work into git

Only on the maintainer's explicit go, for exactly the commits named. The coordinator commits, or the
role that owns the commit plan.

1. `git status`: if another role has unstaged changes in hook config or in files you commit, stop
   and ask.
2. Stage by hunk without touching the working tree: `git apply --cached <patch>`, or
   `git hash-object -w` plus `git update-index --cacheinfo` for a whole prepared blob. No
   interactive staging.
3. Without a git identity in the container, commit with `git -c user.name=… -c user.email=…`, taking
   the values from the maintainer's previous commits (`git log -1 --format='%an <%ae>'`). Never
   write them into config or files.
4. Hooks that rewrite files (end-of-file, line endings, mdformat) fail the first attempt: re-stage
   and commit again. `--no-verify` only on the maintainer's word.
5. Conventional Commits, checked with `conventional-pre-commit --strict`. Messages cite records by
   absolute ID (`0.1.0:D0018`); no IDs from gitignored documents (F-nn, CH-nn, m-n).
6. Check that every planned hunk landed (`git show --stat`, a diff against the plan) and that the
   tests pass at each commit (side worktree if needed). Never push without a separate go.

## Container rebuilds and session ends

A container rebuild is a pause "now" (see "Pausing"). Subagents and in-process teammates do not
survive it, so the coordinator lets them finish first. The coordinator also backs up Claude memory
to `.agents/tmp/claude-memory/`. After the rebuild, run `poetry install --all-extras` and the test
suite before trusting anything.
