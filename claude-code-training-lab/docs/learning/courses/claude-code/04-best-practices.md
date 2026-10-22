# Lesson 4: Best practices for Claude Code

- **Course:** Claude Code docs (lesson 4)
- **Source:** https://code.claude.com/docs/en/best-practices
- **Date:** 2026-10-20
- **Status:** In progress

All exercises use ReviewRadar as the project. Run them in Claude Code (terminal or desktop), folder `claude-code-training-lab`. Do not commit and do not push; revert each change before the next exercise with `git checkout .` (and `git clean -n` to see new files first). Edits to `.claude/` files in Ex 5 and 6 are proposals only: ask Claude to show the change, do not apply it.

## Exercises

### Ex 1: Give Claude a way to verify

**Where:** Claude Code, permission mode **Manual**. Revert afterwards.

**Initial prompt:**
```
add a function that validates a rating
```

**Improved prompt:**
```
Add a function validate_rating(value: int) -> int in reviews/services.py that returns the value when it is 1 to 5 and raises ValueError otherwise. Test cases: 1 and 5 pass, 0 and 6 raise, True raises (a bool is not a rating). Write the tests first in reviews/tests/unit, run them red, then implement, then run: uv run ruff check . && uv run mypy . && uv run pytest -q --no-cov. Show me the output of each command, not a summary.
```

| Question | Your answer |
|---|---|
| Was the test red before the code and green after? | |
| Did Claude show the real command output (evidence) or only say "done"? | |
| Which edge case did the check catch that the first prompt would have missed? | |

### Ex 2: Explore, plan, code, commit (without the commit)

**Where:** Claude Code. Phase 1 and 2 in **Plan** mode (`Shift+Tab` until `⏸ plan mode on`), phase 3 in **Accept edits**. Revert afterwards.

**Phase 1, explore:**
```
Read reviews/services.py, reviews/repositories.py and reviews/forms.py. Explain how the reviews page applies the filters and the pagination. Do not change any files.
```
**Phase 2, plan:**
```
I want a filter by minimum rating (1 to 5) on the reviews page. Which files change? What is the data flow from the request to the query? Which tests are needed (include the query count)? Create a plan and stop.
```
Press `Ctrl+G` to open the plan in your editor and remove one step you do not want.

**Phase 3, implement:**
```
Implement the plan, tests first. Run the checks and show me the output.
```
**Phase 4:** ask only for a **draft** commit message that follows `.claude/rules/git.md`. Do not run `git commit`.

| Question | Your answer |
|---|---|
| What did the plan include that you would have forgotten? | |
| How much did removing a step in the editor change the result? | |
| When would you skip planning for this repo (one-sentence diff)? | |

### Ex 3: Specific prompts, four strategies

**Where:** Claude Code, read-only (Plan mode).

Write the "after" version of each weak prompt for ReviewRadar, run both, and compare.

| Strategy | Weak prompt | Your "after" prompt | What changed in the answer |
|---|---|---|---|
| Scope the task | `add tests for services.py` | | |
| Point to a source | `why is the score rounded like that?` | (hint: git history and `.claude/knowledge/KNOWN_PITFALLS.md`) | |
| Reference an existing pattern | `add a new filter` | (hint: name one existing filter as the pattern) | |
| Describe the symptom | `fix the dashboard bug` | (hint: symptom, likely place, what "fixed" looks like) | |

### Ex 4: Rich content

**Where:** Claude Code, read-only.

1. `@` a file: `Explain @reviews/services.py in 5 lines.`
2. Paste a screenshot of the dashboard and ask what is on it.
3. Pipe data (terminal): `git log --oneline -15 | claude -p "which commits touch the score rule? answer with the hash and one line each"`
4. Let Claude fetch: `Run the tests and tell me which ones are slow. Use the command line, do not guess.`

| Question | Your answer |
|---|---|
| Which way cost the least context? | |
| Which way gave the most precise answer? | |

### Ex 5: Audit the project CLAUDE.md

**Where:** Claude Code, read-only. **Do not apply the cuts.**

1. Run `/context` and note how much the memory files (`CLAUDE.md`, `rules/`, `context/`) take.
2. Run `/doctor`. Read what it proposes to cut.
3. Prompt:
```
Review .claude/CLAUDE.md with one test for each section: "would removing this cause Claude to make mistakes?" Give a table: section | keep, move to a skill, move to a rule, or cut | one-line reason. Do not edit any file.
```

| Section | Keep / skill / rule / cut | Reason |
|---|---|---|
| Quick orientation | | |
| Where things live | | |
| AI engineering lifecycle | | |
| Available skills (table) | | |
| Available commands (table) | | |
| Removed, and why | | |

Then decide, in the table below, which rule is advisory in text but should be a hook (a guarantee).

| Rule | Today | Should be a hook? |
|---|---|---|
| Never commit to `main` | | |
| No `Co-Authored-By` in commits | | |
| One repository only on GitHub | | |

### Ex 6: Permissions, CLI tools, MCP, hooks, skills, subagents

**Where:** Claude Code. Look, do not change.

| Tool | Command or prompt | What you found in this repo |
|---|---|---|
| Permissions | `/permissions` | |
| Sandbox | `/sandbox` | |
| MCP | `/mcp` (and `.mcp.json`) | |
| Hooks | `/hooks` | |
| Skills | type `/` | |
| Subagents | `/agents` | |
| Plugins | `/plugin` | |

Prompt to write a hook as a proposal only:
```
Propose (do not write) a hook that runs ruff on every Python file after an edit in this repo. Show the settings.json entry and the script, and say which existing hook in .claude/hooks/ it would sit next to.
```

### Ex 7: Let Claude interview you

**Where:** Claude Code, **Plan** mode.

**Prompt:**
```
I want to add a score trend per branch (planned in the README). Interview me in detail using the AskUserQuestion tool. Ask about the data, the page, edge cases (no reviews, one review, a branch with a gap week), and trade-offs. Don't ask obvious questions. When we are done, write a complete spec to docs/app/trend-spec-draft.md.
```
Answer the questions, then read the spec. Delete the draft file afterwards (it is not part of the repository).

| Question | Your answer |
|---|---|
| Which question surprised you? | |
| Does the spec name files, say what is out of scope and end with an end-to-end check? | |

### Ex 8: Manage the session

**Where:** Claude Code

| Control | Try | What happened |
|---|---|---|
| `Esc` | Start a long answer and press `Esc`, then redirect | |
| `Esc Esc` or `/rewind` | Make a change, rewind code only, then conversation only | |
| `/clear` | Between two unrelated questions | |
| `/compact` | `/compact Focus on the filter changes` | |
| `/btw` | Ask a side question; check it does not stay in the history | |
| `/rename` | Name the session `best-practices-ex8` | |
| `claude --resume` | Find it again | |

Note: checkpoints do not track changes made by shell commands, so they do not replace git.

### Ex 9: Subagents, writer and reviewer, `-p`

**Where:** Claude Code and the terminal

1. **Investigate with a subagent:**
```
Use a subagent to investigate how the week filter handles the Asia/Ho_Chi_Minh time zone and report only the file, line and rule.
```
2. **Writer and reviewer:** in session A implement a small change (from Ex 1). In a **new** session B:
```
Review the diff of the last change against the rules in .claude/rules/. Report only gaps that affect correctness or the stated requirement, not style.
```
Or run `/code-review`.
3. **Non-interactive:**
```bash
claude -p "List all Django views in this project" --output-format json
```

| Question | Your answer |
|---|---|
| What did session B find that session A missed? | |
| Did B report style opinions you would ignore? | |
| What does the `json` output contain besides the answer? | |

### Ex 10: Spot the failure pattern (paper exercise)

Name the pattern and the fix for each case.

| # | Situation | Pattern | Fix |
|---|---|---|---|
| 1 | One session: fix the score, then a README question, then a new filter, then back to the score | | |
| 2 | You corrected the same mistake three times and it is still wrong | | |
| 3 | CLAUDE.md has 400 lines and the commit rule is ignored | | |
| 4 | The new page "looks right" but nobody ran a test or a screenshot | | |
| 5 | "Investigate why the dashboard is slow", Claude reads 200 files | | |

Expected: 1 kitchen sink session, `/clear` between tasks; 2 correcting over and over, `/clear` and a better first prompt; 3 over-specified CLAUDE.md, prune or turn the rule into a hook; 4 trust-then-verify gap, add tests, scripts or screenshots; 5 infinite exploration, scope it or use a subagent.

## Key takeaways

- **One constraint drives most of the advice: the context window.** It fills fast and quality drops as it fills. Treat context as the scarce resource.
- **Verify first.** Give Claude a check it can run (tests, build, linter, screenshot) and ask for the real output as evidence. Steps up: in the prompt, `/goal` for a whole session, a Stop hook as a hard gate, a second subagent as reviewer.
- **Explore, plan, implement, commit.** Use plan mode when the approach is uncertain, several files change, or the code is new to you. If the diff fits in one sentence, skip the plan. `Ctrl+G` edits the plan in your editor.
- **Be specific:** scope the task, point to sources, reference an existing pattern, describe the symptom. A vague prompt is fine when you are exploring.
- **Rich context:** `@file`, pasted images, URLs, piped data (`cat log | claude -p`), or let Claude fetch it with commands.
- **CLAUDE.md:** short and broad. Ask of each line "would removing this cause a mistake?" Put commands Claude cannot guess, style that differs from defaults, repository etiquette, architecture decisions and gotchas in. Leave out what the code shows, long tutorials and anything that changes often. Sometimes-needed knowledge goes in a skill. `/init` starts one, `/context` and `/doctor` check it.
- **Advice versus guarantee:** CLAUDE.md is advisory; **hooks are deterministic**. A rule that must hold every time belongs in a hook.
- **Extensions:** permissions allowlist and sandbox (fewer prompts), CLI tools like `gh` (cheapest in context), MCP servers, skills (`SKILL.md`, `disable-model-invocation: true` for side effects), custom subagents, plugins.
- **Interview before building:** have Claude ask you questions and write a spec, then execute it in a fresh session.
- **Session control:** `Esc` stops, `Esc Esc` or `/rewind` restores conversation and code, `/clear` between tasks, `/compact <focus>` to condense, `/btw` for side questions, `/rename` and `--resume` for long work. Checkpoints are not a replacement for git.
- **Scale:** `claude -p` in scripts and CI, worktrees and parallel sessions, `/batch` or a loop for fan-out (`--allowedTools`, `--permission-mode dontAsk`), auto mode with a safety classifier.
- **Fresh eyes:** a reviewer in a new context (a subagent, `/code-review`) judges the diff without the writer's reasoning. Ask it for correctness gaps only, or it will push over-engineering.
- **Five failure patterns:** kitchen sink session, correcting over and over, over-specified CLAUDE.md, trust-then-verify gap, infinite exploration.
- **Intuition beats rules:** these are starting points. Notice what you did when the result was good.
