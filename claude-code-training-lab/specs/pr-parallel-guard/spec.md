# Spec: pr-parallel-guard

## Summary

Four guards against clashes between pull requests the loop builds in parallel: the tick reads every number of `Depends on`, the tick waits when a new issue would touch a file that an issue in progress or in review already touches, the tick starts no new issue while `main` is red, and the loop may fix a conflict by merging `main` into its branch when the owner asks with `/redo`. The owner switches on a GitHub ruleset on `main` so GitHub itself refuses to merge a pull request that is behind `main` or red. Nothing visible to users of the app.

## Acceptance criteria

### Tick (`ops/`)

- **AC1. Every `Depends on` number.** The tick reads every `#<number>` on each line of the issue body that starts with `Depends on` (for example `Depends on #63, #61 (both change settings.py)` gives 63 and 61). The issue is not taken while any of them is open. A body with no such line has no dependency.
- **AC2. Files of an issue.** The files of an issue are the backticked paths in the bullet lines of its `## Files likely touched` section (up to the next `##` heading). A trailing note such as `(NEW)` or `(only the robots meta line)` is ignored; the path is the text between the first pair of backticks on the line. Paths are compared as written, after removing a leading `./` and a leading `claude-code-training-lab/`.
- **AC3. Wait on shared files.** A new `agent:ready` issue is not taken when one of its files (AC2) is also a file of an open issue labelled `agent:running` or `agent:review`, or of an issue already chosen earlier in the same tick. The tick writes one line in its log naming the issue, the other issue and the shared file, and goes on to the next ready issue. The issue is taken at a later tick once the other issue is closed (its pull request merged) or no longer has those labels.
- **AC4. No files listed.** An `agent:ready` issue with no `## Files likely touched` section, or one with no backticked path in it, runs alone, as `risk:high` does today (ADR-014): it starts only when no other build runs, and no other new issue starts while it runs.
- **AC5. Red `main`.** At the start of each tick, the tick reads the most recent completed run of the `Checks` workflow on `main` (`gh run list --workflow checks.yml --branch main --status completed --limit 1 --json conclusion,headSha,url`). When its conclusion is not `success`, the tick starts no new issue in that tick; pull request runs (AC4 of `specs/loop-concurrency/spec.md`) still start. It sends one ntfy message "main is red at <short sha>: <run url>", and does not send it again for the same commit. When the read fails, the tick goes on as if `main` were green and writes one log line.
- **AC6. Tests.** A new test file `ops/tests/test_tick_guards.py` covers AC1 to AC5 with `gh` and the clock faked (no network), including: `Depends on #63, #61` with #61 open; two issues sharing `reviews/services.py`; a path with a `(NEW)` note and with the `claude-code-training-lab/` prefix; a ready issue overlapping an `agent:review` issue; an issue without the section; a red, a green and an unreadable `main` run; the red message sent only once per commit. Existing tests in `ops/tests/test_agent_tick.py` stay unchanged and pass. `uv run ruff check .` and `uv run mypy .` pass.
- **AC7. How to run.** `ops/README.md` says, in a short "Guards" part, when the tick waits (AC1, AC3, AC4, AC5) and where the log line is.

### Merge order, conflicts and records (`.claude/`, `docs/`)

- **AC8. One merge at a time.** The Merge step in `.claude/project-instructions.md` merges one build pull request at a time. Before each merge it runs `gh pr update-branch <n>` when the pull request is behind `main`, waits for CI on the new head and merges only when it is green (as today). After a clean update, green CI is enough; the verify report is not built again.
- **AC9. Conflict goes back to the loop.** When `gh pr update-branch` fails because of a conflict, the merge thread does not merge. It posts on the pull request, with the owner's login, the comment `/redo merge origin/main into this branch and fix the conflict`, runs one tick at once, and tells the owner the pull request is waiting for the redo. The owner's OK for that pull request has to be given again after the redo.
- **AC10. The loop fixes the conflict.** In `.claude/skills/work-queue/SKILL.md`, section 1, a `/redo` that asks to merge `main` is done by `git fetch origin main` and `git merge origin/main` on the pull request branch (never a rebase, never a force-push), fixing the conflict, then the full round: tests and gates, review, the same report updated and republished to the same link, push, wait for CI. A conflict met without such a `/redo` still gets `pr:blocked` as today. A conflict the loop cannot fix without changing the requirement gets `pr:blocked` with the reason.
- **AC11. Files listed in every task.** `docs/app/templates/spec/tasks.md` and the issue rules in `.claude/project-instructions.md` say that every issue body has a `## Files likely touched` section with one backticked path per bullet line, because the tick reads it (AC2 to AC4).
- **AC12. Branch protection.** ADR-015 records that the repository is public, so a GitHub ruleset on `main` costs nothing, and gives the owner's one-time steps (Settings, Rules, Rulesets, New branch ruleset): target the default branch; require a pull request before merging; require status checks to pass with the check `checks` and "Require branches to be up to date before merging"; block force pushes; restrict deletions; no bypass list. It says which lines of ADR-008, ADR-010 and ADR-012 ("no branch protection, paid plan") it replaces. Claude does not change repository settings (`rules/security.md`); the owner does.
- **AC13. Recorded.** ADR-015 also records AC1 to AC10 and the rejected options (see Decisions). `knowledge/decisions/README.md` lists ADR-015. `.claude/CLAUDE.md` gets a row in "Removed, and why" for "a conflict with `main` is always `pr:blocked`".

## Edge cases

- Empty: no ready issue, or every ready issue waits on a shared file: no new build; the "queue empty, N pull requests waiting" message of ADR-014 works as today (the waiting issues move once the owner merges).
- Large data: at most 200 open issues are read, as today; the file comparison is per tick and needs no extra `gh` call beyond the one issue list (the `body` field is already read).
- Permissions: only the owner's `/redo` counts (as today), so text in issues cannot ask the loop to merge `main`. The ruleset is switched on by the owner; Claude only writes the steps.
- Two issues that list no files: each runs alone (AC4), so they never run together.
- A file shared with a closed issue: not a clash; that work is on `main` already.
- `main` red because of a pull request run still in progress: only completed runs count (AC5).
- The ruleset makes a merge of a pull request that is behind `main` fail with a clear GitHub message; the merge thread then runs AC8.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Which issues the tick compares files with | Issues `agent:running` and `agent:review`; an issue with no files runs alone | Only `agent:running` | The second build then starts from the new `main`, so its report is never stale for shared files |
| Q2. A conflict when updating the branch | The merge thread posts `/redo merge origin/main …`; the loop merges `main`, fixes, retests, updates the report | Keep `pr:blocked` and leave it to the owner; rebase | A rebase needs a force-push, which the guardrails forbid; the owner does not want to fix conflicts by hand |
| Q3. Report after a clean update of the branch | Green CI on the new head is enough | Always `/redo` a full re-verify | With Q1, two pull requests in review never share a file; a full re-verify costs a build of 10 to 45 minutes |
| Q4. Branch protection | The owner switches on a ruleset on `main` (pull request, `checks` green and up to date, no force push, no bypass) | Hooks only | The repository is public, so it is free; it also guards a merge clicked on GitHub, which the hooks and the merge step do not see |
| Q5. `main` red after a merge | The tick starts no new issue and sends one ntfy per red commit | Rely on GitHub's e-mail | New builds from a red `main` would all go red too |

## Design

Nothing visible to users.

## Open questions
