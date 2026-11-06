# Spec: flow-risks

## Summary

Six small changes to the flow; nothing visible to users of the app. One CI check (T1), three tick changes in `ops/agent_tick.py` (T2 to T4), one work-queue skill change (T5), one bootstrap template rename (T6), and the docs and issue rules (T7).

## Acceptance criteria

### Plugin version (T1)

- **AC1.** `ops/check_plugin_version.py <base> <head>` exits 1 and prints `plugins/agent-flow/ changed but .claude-plugin/plugin.json still has version <v>` when `git diff --name-only <base>...<head>` lists a file under `plugins/agent-flow/` and the `version` in `plugins/agent-flow/.claude-plugin/plugin.json` is the same at both commits.
- **AC2.** It exits 0 when no file under `plugins/agent-flow/` changed, or when the version differs.
- **AC3.** `.github/workflows/checks.yml` runs it on `pull_request` events only, against the pull request's base commit, with enough history for the diff (`fetch-depth: 0`). On `push` to `main` the step is skipped.

### Worktrees of closed work (T2)

- **AC4.** Each tick, for each folder `~/.reviewradar/worktrees/issue-<n>` whose issue is closed, and each `pr-<n>` whose pull request is closed or merged, the tick renames the folder's checked-out branch to `archive/<branch>-<unix time>` (as `archive_branches` does today), runs `git worktree remove --force <folder>`, and logs `<key>: closed, worktree removed`.
- **AC5.** A moved-aside folder `<key>-<unix time>` older than 3 days (by that time) is removed the same way, whatever the state of its issue or pull request.
- **AC6.** A folder of a build that is running (`running_keys`), or of an issue or pull request that is still open, is never removed. Nothing is deleted from git: no branch is deleted.
- **AC7.** At most 10 folders are removed per tick; a failed `git worktree remove` is logged and the tick goes on.

### Stale runs (T3)

- **AC8.** `start` writes the start time (`tick.host.now()`, whole seconds) to a file `started` in the run folder next to `pid`. `running_keys` and `finish_runs` treat a run whose `started` time is more than `RUN_LIMIT` plus 15 minutes before `tick.host.now()` as ended, even when `os.kill(pid, 0)` succeeds. A run folder without a `started` file (started before this change) is judged by the pid alone, as today. No process is signalled. The time comes from the host clock, never from a file's mtime, so the existing tests with a faked clock keep passing unchanged.
- **AC9.** Such a run ends with outcome `gone` (no `exit` file) or its `exit` file's value, and is handled by `handle_end` as today (agent:failed, comment, failure record kind `transient`), so the normal retry applies.

### No retry after a decision stop (T4, T5)

- **AC10.** When a build stops without a pull request because the issue cannot be built as written (contradicting ACs, an AC that needs a change outside the issue, a missing decision), the work-queue skill posts its stop comment with the first line `<!-- work-queue -->` and the second line `<!-- needs-decision -->`, then the reason and the choices for the owner. (T5)
- **AC11.** When such a build ends, the tick records the failure with kind `decision` if a comment on the issue posted after the run started (the run folder's `pid` file time) holds both `<!-- work-queue -->` and `<!-- needs-decision -->`. The tick's own end comment is posted after this check. (T4)
- **AC12.** `retry_reason` returns no reason for a record of kind `decision`, whether `main` or a parent pull request moved. The owner restarts it by adding `agent:ready` again (already handled by `tidy_failed` as "restarted by hand").
- **AC13.** The tick's ntfy message for such an end is `ReviewRadar #<n> needs your decision: <issue link>`, sent once.

### Template test (T6)

- **AC14.** The template is renamed to `ops/bootstrap_stubs/test_flow_config.py.stub`; `ops/bootstrap.py` still writes it to `tests/test_flow_config.py` in the new project, with `{repo}` replaced.
- **AC15.** `uv run pytest ops -q --no-cov -p no:cacheprovider` on main collects no file under `ops/bootstrap_stubs/` and passes.

### Docs and issue rules (T7)

- **AC16.** `.claude/CLAUDE.md` and `ADR-014` say the tick runs every 5 minutes; no file outside `specs/` and `docs/learning/` says the tick runs every 10 minutes.
- **AC17.** `.claude/project-instructions.md` adds to the issue rules and the Definition of Ready: before an issue is posted, search the tests for assertions on the behaviour the issue changes. When there are any, the issue lists them under `## Existing tests that change` (one backticked `path::test_name` per bullet), an AC allows exactly those to change, and the issue never says "every existing test passes unchanged". Such an issue stays `agent:ready` when every listed test is outside `checks.protected_test_dirs`, and is `agent:manual` otherwise.
- **AC18.** The work-queue skill's rule on existing tests says the build may edit an existing test only when the issue lists it under `## Existing tests that change`. (T5)

## Edge cases

- Empty: no worktrees, no runs, no failure records: the tick does nothing new and logs nothing new.
- Large data: AC7 caps removals at 10 per tick; the 29 folders today go in three ticks.
- Permissions: the tick runs as the owner on the Mac mini; `git worktree remove --force` drops uncommitted changes of a closed build only, its commits stay on the `archive/` branch.
- A worktree with no branch (detached): removed without a rename.
- A run whose `pid` file is missing: unchanged (skipped, as today). A `started` file that is not a number: judged by the pid alone.
- A decision marker from an earlier run: ignored, only comments posted during this run count.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 How CI enforces the plugin bump | A script compares the version at base and head when `plugins/agent-flow/` changed | A test with a stored content hash | States the rule directly; no extra file to keep in step |
| Q2 When the tick removes a kept worktree | Issue or pull request closed; moved-aside folders after 3 days; branch archived first | Also failed builds of open issues after 14 days; only report the size | Closed work needs no checkout; commits stay on the archive branch |
| Q3 Fallback for a stale pid | Run started more than 45 + 15 minutes ago (time written by the tick) counts as ended, nothing is killed | Compare the process start time with `ps` | Simple, no macOS-specific parsing; a real build is stopped at 45 minutes |
| Q4a How a build says "needs the owner" | A `<!-- needs-decision -->` line in its stop comment | A new label `agent:needs-decision` | No new label; the comment is written today |
| Q4b Issues that change what existing tests assert | Name them; `agent:ready` outside protected test folders, `agent:manual` inside | Always `agent:manual` | The hook already allows edits outside `reviews/tests/`; the loop keeps the work |
| Q5 Template test collected by `pytest ops` | Rename to `.stub` | `norecursedirs` in `pyproject.toml` | No gate-file change |

## Design

Nothing visible to users.

## Open questions
