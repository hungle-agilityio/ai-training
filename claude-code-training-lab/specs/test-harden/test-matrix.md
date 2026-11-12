# Test matrix: test-harden

Written from the ACs of `spec.md` before any build. No AC here is seen on the app's pages, so every check is in the plain form; the empty cases of the flow (no sensitive path, no finding, no client-facing pull request) are `edge` rows.

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | A config with `[paths] review_sensitive = ["reviews/models.py"]` gives `paths_review_sensitive == ("reviews/models.py",)` | unit | `ops/tests/test_flow_config_review_sensitive.py` | T1 |
| M2 | AC1 | edge | A config without the key gives `()`; `review_sensitive = [1]` raises `FlowConfigError` naming `paths.review_sensitive` | unit | same | T1 |
| M3 | AC2 | normal | `ops/flow.toml` lists the ten patterns of AC2 in order, and no other `[paths]` key | unit | same | T1 |
| M4 | AC3 | normal | In a fixture repository, a branch that changes `<app>/reviews/models.py` prints `high` and `  <app>/reviews/models.py  (reviews/models.py)`; a change to `render.yaml` at the root matches `../render.yaml`; exit 0 | unit | `../plugins/agent-flow/skills/work-queue/tests/test_review_level.py` | T1 |
| M5 | AC3 | edge | A branch that changes only `<app>/reviews/views.py` prints `standard`; a bad `--base` exits 2 with `review_level:` | unit | same | T1 |
| M6 | AC5 | normal | work-queue step 9 names `review_level.py`, the `code-review` skill at `medium` and `high`, `reviewer` on `high`, fix or dismiss with a reason, at most two rounds, `agent:failed` after round 2 | unit | `../plugins/agent-flow/tests/test_code_review_texts.py` | T2 |
| M7 | AC6 | error | work-queue says the fallback to `reviewer` and the line `/code-review did not run: <reason>; reviewer only.` | unit | same | T2 |
| M8 | AC7 | normal | `draft_pr.py --code-review FILE` puts `## Code review` with the file's text right after `## How tested` and before the tests-changed section | unit | `../plugins/agent-flow/skills/draft-pull-request/tests/test_code_review_section.py` | T2 |
| M9 | AC7 | edge | Without `--code-review` the body is byte-for-byte the body of `main` for the same input | unit | same | T2 |
| M10 | AC8 | normal | work-queue has the section Epic review with the prompt text, `high` on `origin/main...HEAD`, one fix attempt per finding, push to the epic branch, the comment markers `<!-- work-queue -->` and `<!-- epic-review -->`, one round only | unit | `../plugins/agent-flow/tests/test_code_review_texts.py` | T2 |
| M11 | AC9 | edge | work-queue says a finding that changes a requirement is `left: changes the requirement of #<n>` | unit | same | T2 |
| M12 | AC10 | normal | `plugin.json` version is one patch above the base branch (`ops/check_plugin_version.py` passes in CI) | manual | CI step "Plugin version is bumped" on the pull request | T2 |
| M13 | AC11 | normal | A green, open epic pull request with no epic-review comment and a free slot is chosen with the prompt `Use the work-queue skill for pull request #<N> only: epic review.` and the message `ReviewRadar reviewing epic PR #<N>` | unit | `ops/tests/test_tick_epic_review.py` | T3 |
| M14 | AC11 | edge | The same pull request is not chosen when it has the comment, when CI is red or running, when it has an open change request, or when it is already running | unit | same | T3 |
| M15 | AC12 | normal | `mark_green_ready` leaves an epic pull request without the comment unlabelled, and labels it `pr:ready-for-review` once the comment exists | unit | same | T3 |
| M16 | AC13 | error | After two runs without the comment (`epic-review-<N>` holds 2), no third run starts, the label is set when green, and the message of AC13 is sent once | unit | same | T3 |
| M17 | AC15 | normal | `ops/regression_screens.json` has the nine steps of AC15 with their names, gotos, actions and expected texts, in order | unit | `ops/tests/test_regression_screens.py` | T4 |
| M18 | AC16 | normal | `checks.yml` has `Install the browser` and `Browser regression of the main screens` with the AC16 commands, after "App tests with coverage"; the triggers are unchanged | unit | same | T4 |
| M19 | AC15, AC16 | normal | The browser regression step is green on the task's pull request (all nine steps OK, `result: clean`) | manual | Checks run of the pull request, step "Browser regression of the main screens" | T4 |
| M20 | AC18 | normal | In a fixture repository, a merge that changes `reviews/views.py` is client-facing and one that changes only `specs/x/spec.md` is internal | unit | `ops/tests/test_release_client_facing.py` | T5 |
| M21 | AC19 | normal | `--dry-run` prints `Client-facing pull requests:` with `  #<n> <title>` of the first merge, then `Internal pull requests:` with the second; no `Merged pull requests:` line | unit | same | T5 |
| M22 | AC19 | edge | With only an internal merge, the client-facing group shows `  (none)` | unit | same | T5 |
| M23 | AC21 | normal | ADR-029 exists with context, decision and rejected options; the decisions README lists it | manual | Read the files on the pull request | T6 |
| M24 | AC22 | normal | `workflow.md` names `/code-review` in every build, `paths.review_sensitive`, the epic review and ultrareview by hand; `uv run pytest ops/tests ../plugins/agent-flow -q --no-cov` passes | manual | Read the diff; the Checks run | T6 |
| M25 | AC23 | normal | `project-instructions.md` Release paragraph names the page link, newest on top, one entry per client-facing pull request, and the line for a release with none | manual | Read the diff; the owner pastes it into Project settings | T6 |
