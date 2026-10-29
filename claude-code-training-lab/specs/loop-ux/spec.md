# Spec: loop-ux

## Summary

Three changes to the loop on the Mac mini, nothing visible to users of the app. (1) The tick sends ntfy for every step that matters, and no longer says "queue empty" when it is waiting on the cap. (2) The tick merges a loop pull request when the owner writes a short approval comment on it; the project chat and the GitHub Merge button lead to the same result, and after any merge the tick pulls `main` and says so. (3) Any owner comment on a loop pull request, including a comment on a line of code, is a change request; the loop marks each one with a reaction and a reply, and only comments without a done mark are open.

Words used below:

- **Loop pull request:** as in AC1 of `specs/tick-hardening/spec.md` (the marker, author `hungle-agilityio`, not from a fork).
- **Owner comment:** a comment whose author login is `hungle-agilityio` and whose body has no `<!-- work-queue -->` line.
- **Approval comment:** an owner comment on the pull request conversation whose whole body, lower-cased, with spaces trimmed and the characters `.!,:;` removed at the end, is one of: `/merge`, `merge`, `lgtm`, `approved`, `approve`, `looks good`, `look good`, `ok`, `duyệt`, `ship it`.
- **Done mark:** a 🚀 (`rocket`) or 😕 (`confused`) reaction by `hungle-agilityio` on the comment.
- **Open change request:** an owner comment on a loop pull request that is not an approval comment, has no done mark, and is either (a) on the pull request conversation, (b) an inline review comment on the pull request (top-level or reply), or (c) a comment on the issue it closes that starts with `/redo`. Comments created before the pull request was opened do not count.

## Acceptance criteria

### Notifications (tick, `ops/`)

- **AC1. Build started.** When the tick starts an issue build, it sends `ReviewRadar started #<n>: <issue title>`. When it starts a pull request run, it sends `ReviewRadar working on PR #<p> (<k> change requests open)`, or `(CI)` when no change request is open.
- **AC2. Needs you.** When a loop pull request has `pr:blocked` or `pr:ci-failed`, the tick sends `ReviewRadar PR #<p> needs you: <label>` and the link `https://github.com/hungle-agilityio/ai-training/pull/<p>`. Sent once per pull request, label and head commit (kept in a file under `~/.reviewradar/`).
- **AC3. Waiting on the cap.** When no build starts, nothing runs, and at least one open issue has `agent:ready` and none of `agent:running`, `agent:review`, `agent:failed`, `agent:manual`, the tick does not send "queue empty". It sends `ReviewRadar waiting: <w> pull requests open (limit <cap>), <k> ready issues not started`, then the link to the open loop pull requests. Like "queue empty", it is sent again only when the text changes. "Queue empty" is sent only when no such issue exists.
- **AC4. Merged.** When a loop pull request is merged (by the tick or on GitHub) and the tick has not announced it yet, the tick first pulls `main` as in AC2 of `specs/tick-hardening/spec.md`, then sends `ReviewRadar PR #<p> merged (#<issue>); main is now <short sha>`, or `...; main checkout not updated: <reason>` when the pull did not happen. Announced pull requests are kept in a file under `~/.reviewradar/`. When that file does not exist yet, the tick records every merged loop pull request it sees and sends nothing for them.
- **AC5. Messages kept.** The messages of #68 (pull request opened or updated), #70 (main is red) and #74 (main not updated, build did not start), and today's "build failed", "paused" and "queue empty" stay as they are. With no `NTFY_TOPIC`, nothing is sent.

### Merge by approval (tick, `ops/`)

- **AC6. When the tick merges.** At each tick, before choosing builds, for every open loop pull request the tick merges it when all of these hold: the newest approval comment is newer than the newest commit of the pull request that is not an update from `main` (a commit whose headline starts with `Merge branch 'main'`); the pull request is not a draft and has `pr:ready-for-review`; it has at least one check and every check is completed with `SUCCESS`, `NEUTRAL` or `SKIPPED`; no change request is open; no run of that pull request is in progress. The merge is `gh pr merge <p> --merge --delete-branch --match-head-commit <head sha>`.
- **AC7. Behind main.** When the conditions of AC6 hold but `mergeStateStatus` is `BEHIND`, the tick runs `gh pr update-branch <p>` and does not merge in that tick. The approval stays valid (AC6 ignores the update commit), so the merge happens at a later tick once CI is green on the new head.
- **AC8. Not merged.** When `gh pr update-branch` fails with a conflict, the tick posts on the pull request, with the owner's login and without the marker, the comment `/redo merge origin/main into this branch and fix the conflict`, so the next tick runs it as a change request; the approval has to be given again after that round. When the merge fails, or `mergeStateStatus` is `DIRTY` or `BLOCKED`, or a check is red, the tick does not merge and sends `ReviewRadar PR #<p> not merged: <reason>` once per pull request and reason. CI that is still running is not a reason: the tick waits.
- **AC9. Marks on the approval.** After a merge the tick adds 🚀 to the approval comment; after a refusal of AC8 it adds 😕. An approval comment with the tick's 🚀 or 😕 is not read again; a new approval comment is needed after a refusal.
- **AC10. Only the owner.** A comment, a reaction or a label from any other login never merges, never asks for a change and never counts as a done mark.

### Change requests (tick `ops/`, work-queue `.claude/`)

- **AC11. The tick picks open requests.** The tick runs a pull request when it has at least one open change request, in place of today's "`/redo` newer than the last commit". The other cases of `pr_needs_run` stay. Reactions are read with `gh api` on `issues/comments/<id>/reactions` and `pulls/comments/<id>/reactions`, only for comments whose reaction summary has a `rocket` or `confused` count above 0.
- **AC12. The loop reads all open requests.** In `.claude/skills/work-queue/SKILL.md`, section 1, the requirement of a round is every open change request of the pull request, oldest first. When a run starts, it adds 👀 to each of them.
- **AC13. The loop marks each one.** For each open change request, at the end of the round, the loop adds 🚀 when it was done, and replies with the marker: `Done in <short sha>: <one line>`. A question is answered in the reply with 🚀 and no commit. When it cannot be done without changing the requirement, or a hook blocks it, the loop adds 😕, replies with the reason, and sets `pr:blocked`. A reply to an inline review comment goes in the same thread, and that thread is resolved once the comment has 🚀. The owner may add 🚀 themselves to tell the loop to skip a comment.
- **AC14. Permissions for the loop.** In loop mode (`REVIEWRADAR_LOOP=1`), `.claude/settings.json` and the hook `before-github-command-check` allow, without asking: `gh api -X POST` on `repos/hungle-agilityio/ai-training/issues/comments/<id>/reactions`, `repos/hungle-agilityio/ai-training/pulls/comments/<id>/reactions` and `repos/hungle-agilityio/ai-training/pulls/<p>/comments/<id>/replies`, and `gh api graphql` with the `resolveReviewThread` mutation only. `gh pr merge` stays refused for loop builds; any other `gh api` stays as today.

### Rules and records (`.claude/`, `docs/`)

- **AC15. Merge step.** The Merge step in `.claude/project-instructions.md` becomes: when the owner approves a named build pull request in the project chat (or the only one waiting), a thread posts the approval comment `/merge` on it through Remote Control with the owner's login, runs one tick at once, and reports what the tick did (merged, waiting for CI, updated from `main`, or not merged and why). It no longer runs `gh pr merge`. The Redo step posts the owner's words as a plain comment (no `/redo` prefix needed). The same text is written to `/mnt/project-files/project-instructions-paste.txt` for the project settings.
- **AC16. ADR-016.** `knowledge/decisions/ADR-016-tick-merges-on-owner-approval.md` records: the tick (plain Python, not a Claude build) merges on the owner's approval comment, with the checks of AC6 to AC10; Claude builds still never merge; change requests are owner comments with done marks (AC11 to AC13); and the decisions table of this spec. It names the lines of ADR-009, `rules/git.md`, `rules/security.md`, `rules/workflow.md` and the work-queue skill that it replaces, and those lines are updated to say "Claude builds never merge; the tick merges on the owner's approval comment (ADR-016)". `knowledge/decisions/README.md` lists ADR-016. `.claude/CLAUDE.md` gets a row in "Removed, and why" for "`/redo` as the only change request" and "merge only through a thread's `gh pr merge`".
- **AC17. How to use.** `ops/README.md` has a short "Review from the phone" part: the approval words, how to ask for a change, what 👀 🚀 😕 mean, and the list of ntfy messages with when each is sent.

### Tests

- **AC18. Tests.** New test files, with `gh`, `git` and the clock faked (no network): `ops/tests/test_tick_notify_cases.py` for AC1 to AC5 and `ops/tests/test_tick_merge.py` for AC6 to AC11, including: `LGTM!` merges, `lgtm but rename X` does not and is a change request; an approval older than a loop commit, and one older only than a `Merge branch 'main'` commit; `BEHIND`, a conflict on update, `DIRTY`, red and running CI; an approval by another login; a 🚀 by another login; a comment from before the pull request was opened; the first run with no announced file. Hook tests for AC14 go in a new file `.claude/hooks/tests/test_loop_review_marks.py`. Existing tests stay unchanged and pass. `uv run ruff check .` and `uv run mypy .` pass.

## Edge cases

- Empty: no loop pull request: no merge, no change request; AC3 or "queue empty" as before.
- Large data: still one pull request list per tick; the extra `gh api` calls are per open loop pull request (at most the cap, 5 after #72) and reactions are read only when the summary shows a mark.
- Permissions: only `hungle-agilityio` counts (AC10); a fork pull request is never a loop pull request (#74).
- Two approval comments: the newest counts. An approval and a change request in the same tick: no merge, the change request runs first.
- The owner edits an old comment: GitHub keeps its creation time, so an edited comment with 🚀 stays done; to ask again, write a new comment.
- The owner presses Merge on GitHub while a run of that pull request is in progress: the run's push fails; the next tick tidies the merged pull request as today and AC4 announces it.
- A merge commit from `main` made by the loop itself when fixing a conflict (`Merge remote-tracking branch ...`) is not an update from `main` for AC6, because it may hold conflict fixes: a new approval is needed.
- At the switch, open loop pull requests with old `/redo` comments that were already done would count as open. There is none open on 2026-10-29; if one is open when T3 merges, the owner adds 🚀 to its old comments.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Which ntfy messages | Nine cases: started, PR opened/updated, needs you, failed or not started, waiting on the cap, queue empty, merged and main pulled, not merged, limit / red main / main not updated | Only the cases that need the owner | The owner listed "tick issues"; about ten messages a day |
| Q2. Which comment approves | A short whole comment from a fixed list (`lgtm`, `approved`, `duyệt`, ...) by the owner | Only `/merge`; any comment containing `lgtm` | Natural to write, but "lgtm but fix X" never merges |
| Q3. Who merges | The tick, for every route: a comment on GitHub, the project chat (a thread posts `/merge` and runs a tick), the GitHub button (tick announces and pulls) | Tick for comments, the thread's `gh pr merge` for the chat | One route with fixed checks in code, and no Claude auto mode in the way |
| Q4. What is a change request | Any owner comment on the pull request, inline comments too, and `/redo` on the issue | `/redo` or inline comments only; `/redo` only | The easiest for the owner; a question is answered without a commit |
| Q5. How a request is marked done | Reactions 👀 / 🚀 / 😕 by the owner's login and a reply; open = no 🚀 or 😕 | A checklist in the pull request body; time of the last commit with a reply | Visible on each comment, does not depend on commits, and the owner can skip one with a 🚀 |

## Design

Nothing visible to users.

## Open questions
