# Lesson 3: Common workflows

- **Course:** Claude Code docs (lesson 3)
- **Source:** https://code.claude.com/docs/en/common-workflows
- **Date:** 2026-10-20
- **Status:** In progress

All exercises use ReviewRadar as the project. Run them in Claude Code (terminal or desktop), folder `claude-code-training-lab`. Do not commit and do not push; revert each change before the next exercise with `git checkout .` (and `git clean -n` to see new files first). Anything that would create a pull request is written as a draft only.

## Exercises

### Ex 1: Understand a codebase, broad to narrow

**Where:** Claude Code, permission mode **Plan** (read-only).

**Initial prompt:**
```
give me an overview of this codebase
```

**Improved prompt** (new session, one message after the other):
```
Without changing any files, give me an overview of reviews/ in 8 lines: the layers and what each one does. Quote file paths.
```
```
Now the key data models and their relations, as a table. Then a glossary of the project terms (branch, location, score, week, good review, bad review) with the file where each is defined.
```
```
Trace the dashboard page from the request to the database: list every function it passes through, with file and line. Stop and say so if a step is unclear instead of guessing.
```

**Check:** compare the answers with `.claude/context/architecture.md` and `.claude/context/domain.md`. Did Claude find anything those files miss?

| Question | Your answer |
|---|---|
| Which layers did it find, in which order? | |
| Is the glossary the same as `domain.md`? | |
| Did the trace pass through the repository (not a query in the view)? | |

### Ex 2: Find relevant code

**Where:** Claude Code, read-only.

**Initial prompt:**
```
find the files that handle filtering
```

**Improved prompt:**
```
Find the code that filters reviews by branch, rating (good or bad) and week. For each filter give the file and line where the input is validated, where the rule is applied, and where the query is built. Use the project terms from .claude/context/domain.md. Do not change any files.
```

| Filter | Validated in | Rule in | Query in |
|---|---|---|---|
| Branch | | | |
| Rating | | | |
| Week | | | |

### Ex 3: Fix a bug from evidence

**Where:** Claude Code, permission mode **Manual**. The repository has bug exercises under `docs/app/issues/bugs/`; use only the report file of one bug (for example `dashboard-wrong-score/01-reported.md`) and do not open the later files (analysis, final).

**Initial prompt:**
```
the dashboard shows a wrong score, fix it
```

**Improved prompt:**
```
Read docs/app/issues/bugs/dashboard-wrong-score/01-reported.md. First write a failing test in reviews/tests/unit that shows the problem, and run it with: uv run pytest -q --no-cov. Then explain the cause with file and line and propose the smallest fix. Do not change the code yet; wait for my OK.
```
After the OK: ask for the fix, run the tests again, then revert.

**Check:** was the test red before the fix and green after? Did Claude name the cause with a file and line?

| Question | Your answer |
|---|---|
| Did the failing test fail for the reason in the report? | |
| What was the cause (file, line)? | |
| How many files did the fix touch? | |

### Ex 4: Refactor safely

**Where:** Claude Code, **Plan** mode first, then **Accept edits**. Revert afterwards.

**Initial prompt:**
```
refactor the services to be cleaner
```

**Improved prompt:**
```
Look at reviews/services.py. Suggest one small refactor that keeps the behaviour the same and respects .claude/rules/architecture.md (no HTTP objects in services, no queries outside repositories). Explain the benefit in 2 lines and name the tests that prove nothing changed. Do not edit yet.
```
Approve, then:
```
Apply it in one small step and run: uv run ruff check . && uv run mypy . && uv run pytest -q --no-cov
```

| Question | Your answer |
|---|---|
| What did the plan name as proof that behaviour is unchanged? | |
| Did ruff, mypy and pytest all pass? | |

### Ex 5: Work with tests

**Where:** Claude Code, **Manual** mode. Revert afterwards.

**Initial prompt:**
```
add tests
```

**Improved prompt:**
```
Find functions in reviews/services.py and reviews/repositories.py that no test covers (use: uv run pytest --cov=reviews --cov-report=term-missing -q). List them, then add tests only for edge cases: no reviews (score is None, not 0), ties in ordering, week boundaries in Asia/Ho_Chi_Minh. Follow the naming in .claude/context/conventions.md. Do not change non-test files.
```

| Question | Your answer |
|---|---|
| Which functions were uncovered? | |
| Which edge cases did Claude add that you did not list? | |
| Did the new tests pass without touching the code? | |

### Ex 6: Documentation and a pull request description (draft only)

**Where:** Claude Code. Nothing is created on GitHub.

**Prompt 1:**
```
Find public functions in reviews/services.py without a one-line docstring. Add one-line docstrings that say the rule, not what the code does, as in .claude/context/conventions.md. Then check that the result follows the project standards.
```

**Prompt 2:**
```
Summarize the changes I made in this session. Then write a draft pull request description in English with What, Why, How tested, Evidence and One concern, following .claude/rules/git.md. Do NOT run gh and do NOT create a pull request. Highlight the risks.
```

**Check:** did Claude keep to "draft only"? Does the description match the format in `.claude/rules/git.md`?

### Ex 7: Images and @ references

**Where:** Claude Code

1. Take a screenshot of the dashboard (run `uv run python manage.py runserver` after loading demo data) and paste it with `Ctrl+V`, or give the path.
2. Prompt:
```
Here is the dashboard. Describe the UI elements, then tell me which element shows the branch score and which file renders it. Start from @reviews/templates and quote paths.
```
3. Try a directory reference (`@reviews/tests`) and a two-file reference (`@reviews/services.py and @reviews/repositories.py`).

| Question | Your answer |
|---|---|
| Did Claude find the template that renders the score? | |
| What does a directory reference give Claude (listing or content)? | |
| Which `CLAUDE.md` files were added to the context by an `@` reference? | |

### Ex 8: Resume, worktree, plan flag, subagent, pipe

**Where:** Terminal

| Command | Try | Result |
|---|---|---|
| Resume | Start a session, ask one question, `/exit`; then `claude --continue` | |
| Picker | `claude --resume` and choose a session | |
| Plan flag | `claude --permission-mode plan`; check the status bar shows `⏸ plan mode on` | |
| Worktree | `claude --worktree try-worktree`; run `git worktree list` in another terminal; then remove it (`git worktree remove`, after checking its path) | |
| Subagent | In a session: `use a subagent to investigate how the score is calculated and report only the file, line and rule` | |
| Pipe | `git log --oneline -20 \| claude -p "summarize these recent commits in 5 lines"` | |

| Question | Your answer |
|---|---|
| In which directory is the worktree created, and on which branch? | |
| What did the subagent return compared with doing the same in the main session? | |

### Ex 9: Pick the right way to schedule (paper exercise)

For each task choose one option: cloud scheduled task, desktop scheduled task, GitHub Actions, or `/loop`. Give a one-line reason.

| # | Task | Your choice | Reason |
|---|---|---|---|
| 1 | Every morning, check open pull requests and post a summary, even when your laptop is off | | |
| 2 | Weekly, audit dependencies using local files and uncommitted work | | |
| 3 | On every opened pull request, run the review | | |
| 4 | For the next 20 minutes, poll whether the workflow run finished | | |

Expected: 1 cloud scheduled task, 2 desktop scheduled task, 3 GitHub Actions, 4 `/loop`.

## Key takeaways

- The page is a set of **recipes**, not a feature tour. Each recipe has the same shape: find, understand, propose, apply, verify.
- **Broad, then narrow.** Start with an overview, then models, then one flow. Ask for the project's glossary, and use the project's own words.
- **Bug fixing:** give the command that reproduces it, the stack trace, and whether it is steady or intermittent. Ask for options first ("suggest a few ways"), then apply one.
- **Refactor** in small testable steps, keep behaviour, and run the tests after each step.
- **Tests:** Claude copies the style of your existing tests. Name the behaviour to check; ask for edge cases (errors, boundaries, odd input).
- **Pull request:** summarize first, then create, then refine the description. Review what Claude wrote and ask it to name the risks. `claude --from-pr <number>` reopens the session linked to a pull request.
- **Docs:** say the style you want (docstrings, JSDoc), ask for examples, check against project standards.
- Claude Code also works in **non-code folders** (notes, documents): the same search and edit.
- **Images** (drag, `Ctrl+V`, or a path) are context for errors, mockups and schemas.
- **`@file`** includes the file; **`@directory`** shows only a listing; an `@` reference also pulls in the `CLAUDE.md` of that folder and its parents; `@server:resource` reads MCP data.
- **Scheduling:** cloud (runs with your computer off), desktop (needs local files), GitHub Actions (repo events), `/loop` (one open session). A scheduled prompt must say what success is, because it cannot ask questions.
- **Ask Claude about itself** ("what skills are available?"); `/powerup` gives interactive lessons.
- **Longer work:** `claude --continue` / `--resume` (or `/resume`) to carry a task across sittings; `claude --worktree name` for isolated parallel sessions (needs at least one commit); `claude --permission-mode plan` or `Shift+Tab` to plan before editing.
- **Subagents** read files in their own context and return only the findings, which keeps the main session clean.
- **`claude -p`** reads stdin and writes stdout like a Unix tool, for CI, hooks and batches.
