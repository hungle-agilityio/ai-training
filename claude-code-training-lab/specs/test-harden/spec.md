# Spec: test-harden

## Summary

Nothing changes on the app's pages. Every loop build runs `/code-review` and fixes its findings; a build that touches a sensitive path (sign-in, data, settings, hosting), listed in `ops/flow.toml`, runs it at high effort plus the `reviewer`. Each epic → main pull request gets one high-effort `/code-review` and one round of fixes on the epic branch before it is marked ready for the owner. CI's Checks open nine main screens in a headless browser on demo data. `ops/release.py` lists client-facing pull requests apart from internal ones, and the release thread keeps one living release notes page for clients.

## User story

As the owner, I want every build and every epic reviewed by `/code-review` (harder when sign-in or data is touched) and fixed before I read it, and the main screens checked in a browser on every change, so that I review less and still trust what reaches `main`.

As a client of ReviewRadar, I want one release notes page that tells in plain words what changed in each release, so that my team knows what it can do now.

## Acceptance criteria

**Sensitive paths and review level (T1)**

- **AC1.** `ops/flow_config.py`: the optional `[paths]` table gets the key `review_sensitive`, a list of glob patterns relative to the app folder (`../` reaches the repository root), read as `FlowConfig.paths_review_sensitive` (a tuple of strings). Its default in `PATH_DEFAULTS` is the empty list, so a project without the key has no sensitive path. A value that is not a list of strings is refused with a `FlowConfigError` that names `paths.review_sensitive`.
- **AC2.** `ops/flow.toml` gets a `[paths]` table with only this key, in this order: `reviews/models.py`, `reviews/migrations/*`, `reviews/repositories.py`, `reviews/*_repository.py`, `reviews/management/commands/*`, `reviews/claude_client.py`, `reviews/templates/registration/*`, `reviewradar/settings.py`, `reviewradar/urls.py`, `../render.yaml`. Every other `[paths]` key keeps its default.
- **AC3.** A new script `../plugins/agent-flow/skills/work-queue/review_level.py --base <ref>` (run from the app folder) reads the flow config the way `route_issue.py` does, lists the files of `git diff --name-only <ref>...HEAD` (paths from the repository root), and compares each with the patterns made root-relative (app folder prefix added, `../` removed; `fnmatch` rules, so `*` also matches `/`). It prints `high` and then one line per matched file (`  <path>  (<pattern>)`) when any file matches, else the single line `standard`. Exit code 0 in both cases; 2 with `review_level: <reason>` when git or the config fails.
- **AC4.** Plugin version: one patch number above the version on the task's base branch (`ops/check_plugin_version.py`). New tests in `ops/tests/test_flow_config_review_sensitive.py` and `../plugins/agent-flow/skills/work-queue/tests/test_review_level.py`; every test on `main` passes unchanged.

**/code-review in every build and on the epic (T2)**

- **AC5.** `work-queue` section 2 step 9 (Review) becomes: run `review_level.py --base origin/<base branch>`; run the `code-review` skill on the branch diff, at `medium` when the level is `standard` and at `high` when it is `high`; also run `reviewer` when `rules/workflow.md` requires it or the level is `high`. Each finding of either is fixed (test first, with `implementer`) or dismissed with a one-line reason a person can check (for example "false positive: the query is in the repository, `reviews/followup_repository.py:40`"). Then tests and gates again and one more review at the same level: at most two rounds. A finding neither fixed nor dismissed after round 2: `agent:failed` and a comment as today.
- **AC6.** When the `code-review` skill cannot run in the build (not available, or it errors twice), the build runs `reviewer` instead, goes on, and writes `/code-review did not run: <reason>; reviewer only.` in the Code review section (AC7).
- **AC7.** `draft-pull-request`: `draft_pr.py` takes `--code-review FILE` and adds a `## Code review` section holding the file's text right after `## How tested` (before the tests-changed section when both are given). Without the flag the body is unchanged. The loop always passes it; the file holds the level line (`Level: standard` or `Level: high (<matched paths>)`), `Rounds: <n>`, and the table `| Finding | File | Result |` with `fixed in <short sha>` or `dismissed: <reason>` per finding, or the single line `No findings.`
- **AC8.** `work-queue` gets a section **Epic review**, run when the tick's prompt is `Use the work-queue skill for pull request #<N> only: epic review.` The worktree is on the epic branch. The run runs the `code-review` skill at `high` on `git diff origin/main...HEAD`, gives every finding one fix attempt (test first, `implementer`, then tests and gates), keeps a fix only when tests and gates pass, commits the fixes (`create-commit`, `Part of #<epic>`), and pushes to the epic branch (no new pull request). It then posts one comment on the pull request whose first line is `<!-- work-queue -->`, second line `<!-- epic-review -->`, then `## Epic review` and the AC7 table (`left: <reason>` for a finding not fixed). It waits for CI and sets the status label as in "After a push". One round only: the run never reviews again.
- **AC9.** A finding whose fix would change what an issue of the epic asks for is never fixed by the run: it is `left: changes the requirement of #<n>` for the owner.
- **AC10.** Plugin version: one patch number above the version on the task's base branch. New tests in `../plugins/agent-flow/tests/test_code_review_texts.py` (texts of AC5, AC6, AC8, AC9) and `../plugins/agent-flow/skills/draft-pull-request/tests/test_code_review_section.py` (AC7); every test on `main` passes unchanged.

**Tick starts the epic review (T3)**

- **AC11.** `ops/agent_tick.py`: an open epic pull request (`is_epic_pr`) whose checks are all green, with no open change request, not running, and with no comment whose body starts with `<!-- work-queue -->` then a line `<!-- epic-review -->`, gets one run with the prompt `Use the work-queue skill for pull request #<N> only: epic review.` in the free slots, before ready issues. Its message is `ReviewRadar reviewing epic PR #<N>`.
- **AC12.** `mark_green_ready` does not set `pr:ready-for-review` on such an epic pull request until it has the epic-review comment; with the comment, everything works as on `main`.
- **AC13.** The tick counts epic review runs per pull request in `<state_dir>/epic-review-<N>`. After two runs that ended without the comment, it starts no more and sets `pr:ready-for-review` as on `main` when CI is green, and sends once `ReviewRadar epic PR #<N>: the epic review did not finish; review it without it: <link>`.
- **AC14.** New tests in `ops/tests/test_tick_epic_review.py`; every test on `main` passes unchanged, except the tests a pinned-test run lists in the issue.

**Browser regression in CI (T4)**

- **AC15.** A new file `ops/regression_screens.json` holds the spec of `check-in-browser` (`{"steps": [...]}`) with exactly these nine steps, in this order, each with its `goto`, its `actions` and its `expect` texts:
  1. `dashboard`, `/dashboard/`: "Reputation dashboard", "Riverside"; `capture` `#kpi-open-cases`.
  2. `location`, `/dashboard/`, click `a[aria-label^='Details for']`: "Weekly trend", "Rating breakdown", "Latest reviews".
  3. `reviews`, `/reviews/`: "Reviews", "Follow-up".
  4. `reply`, `/reviews/?rating=bad`, click `a[href$='/reply/']`: "Reply to a review", "Follow-up", "Template".
  5. `replies`, `/replies/`: "Reply drafts".
  6. `settings`, `/settings/`: "Settings", "Locations", "Location goals", "Reply templates".
  7. `reports`, `/reports/`: "Monthly report".
  8. `compare`, `/compare/`: "Compare locations".
  9. `topics`, `/topics/`: "Topics".
  
  On `main` (d7738b4) this spec gives `result: clean`, exit code 0 (run on 2026-11-12 for this spec).
- **AC16.** `../.github/workflows/checks.yml` gets two steps after "App tests with coverage": `Install the browser` (`uv run playwright install --with-deps chromium`) and `Browser regression of the main screens` (`uv run python .claude/skills/check-in-browser/browser_check.py --spec ops/regression_screens.json`). The step fails on any exit code other than 0, so Checks are red on a missing text, a console error, a failed request or a masking finding. Every other step and the triggers stay as on `main`.
- **AC17.** New tests in `ops/tests/test_regression_screens.py` check AC15 (the nine step names, gotos and expected texts, in order) and AC16 (the two steps, their commands, after the app tests); every test on `main` passes unchanged.

**Client-facing pull requests in the release (T5)**

- **AC18.** `ops/release.py`: a merged pull request is client-facing when its merge commit changed at least one file under `paths.code_dirs` of the flow config (`git diff --name-only <merge>^1 <merge>`, paths under the app folder); otherwise it is internal.
- **AC19.** The plan output replaces the line `Merged pull requests:` with two groups, in this order: `Client-facing pull requests:` and `Internal pull requests:`, each with its lines `  #<n> <title>` in merge order as today, or `  (none)`. Every other line of the output stays as on `main`.
- **AC20.** New tests in `ops/tests/test_release_client_facing.py` (a fixture repository with one merge that changes `reviews/views.py` and one that changes only `specs/x/spec.md`); every test on `main` passes unchanged, except the tests a pinned-test run lists in the issue.

**Project rules (T6, built by hand)**

- **AC21.** `.claude/knowledge/decisions/ADR-029-test-and-harden.md` records the decision (context: Day 14 of the training, the audit of 2026-11-12; decision: AC1 to AC20 and the release notes page; ultrareview stays manual; reverses "Release notes pages" in the out-of-scope list of `specs/release-deploy/intent.md`; rejected options of Q1 to Q5 below). `.claude/knowledge/decisions/README.md` lists it.
- **AC22.** `.claude/rules/workflow.md`: the difficulty table and the triggers say every loop build runs `/code-review` (high plus `reviewer` on a sensitive path, `paths.review_sensitive`), and the Modes say each epic → main pull request gets one epic review before it is ready for the owner; the owner may run ultrareview by hand on any pull request.
- **AC23.** `.claude/project-instructions.md`, the Release paragraph: after `release.py` succeeds, the thread updates the living release notes page https://claude.ai/artifact/9YeTDzCKwuvkYq2jDphaye (republished at the same link, newest release on top, English): one section per release, `Release of <d Month yyyy>` with the tag, one entry per client-facing pull request written from its issue's user story and ACs (what users can do now, and where), internal pull requests not listed. With no client-facing pull request the section says `No changes on your screens in this release.` The page stays private; the owner shares it. After the merge the owner pastes the same text into Project settings (the thread gives the exact text).

## Edge cases

- Empty: a build with no finding writes `No findings.`; a release with no client-facing pull request adds the line of AC23; a project without `paths.review_sensitive` reviews every build at `standard`.
- Large data: an epic with many tasks gets one review of the whole epic diff, not one per task; the regression runs nine screens on the fixed demo data, so its time does not grow with the app's data.
- Permissions: only the tick starts an epic review; the run pushes only to the epic branch and never merges (the hook refuses `gh pr merge` and pushes to `main`).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Where does the loop run `/code-review`? | Every build; `high` plus `reviewer` on a sensitive path | Only on auth/data; replacing `reviewer` | What Day 14 asks; a small cost per build; the independent reviewer stays for risky work |
| Q2 What counts as touching auth/data? | A list of path patterns in `ops/flow.toml` (`paths.review_sensitive`) | The `risk:high` label | Decided from the files really changed, so a wrong risk label cannot hide it |
| Q3 Does Claude review the epic → main pull request? | Yes: the tick starts one `/code-review high`; the loop fixes in one round; the rest goes to the owner in a comment | Findings only, owner decides; no review | Catches problems between tasks that no task review sees; the owner reads only what is left |
| Q4 Where does the QA regression run? | In Checks (CI), in a headless browser, on every pull request and push | Only before a release on the Mac mini; nightly in the tick | What Day 14 asks; catches the break in the pull request that made it; a release already waits for green Checks |
| Q5 How are the release notes kept? | One living page at one link, newest release on top, English, client-facing pull requests only | A new page per release; Vietnamese and English | Clients keep one link; the page already exists in that form |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users of the app. The release notes page: https://claude.ai/artifact/9YeTDzCKwuvkYq2jDphaye (private).

## Open questions
