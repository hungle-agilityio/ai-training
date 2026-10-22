# Lesson 6: Routines and headless

- **Course:** Claude Code in action (lesson 6 of 9, ~7 min)
- **Source:** https://academy.claude.com/courses/claude-code-in-action/routines-and-headless
- **Date:** 2026-10-20
- **Status:** In progress

The lesson has no exercises of its own. These exercises are written for this lab and use ReviewRadar. Run them in the terminal, folder `claude-code-training-lab`. They stay on the machine and are read-only. **Do not create a routine, do not push, do not change `.github/` or any setting**: a routine runs in the cloud on a clone of the repository and may push a `claude/` branch, so creating one is an outward action that needs its own approval. Ex 6 and 7 are paper or proposal only. Revert anything by accident with `git checkout .` (and `git clean -n` to see new files first). Never put a real key or token into a command; use a throw-away shell variable or none at all.

## Exercises

### Ex 1: One-shot run that pipes like a shell tool

**Where:** Terminal

```bash
git log --oneline -15 | claude -p "summarize these commits in 5 lines, grouped by theme"
```
Then a second run with context from a file:
```bash
claude -p "which Django views are defined in reviews/views.py? give the function names only" 
```

| Question | Your answer |
|---|---|
| Did it start an interactive UI? (expected: no, it prints and exits) | |
| Did the second run know about `.claude/CLAUDE.md` without you adding it? (`-p` loads hooks, skills, plugins, MCP servers and CLAUDE.md) | |
| What happens to the shell exit code when the run fails? (try a bad flag and run `echo $?`) | |

### Ex 2: Structured output with a JSON schema

**Where:** Terminal. Needs `jq` (`brew install jq` if missing).

```bash
claude -p "Extract the names of the public functions in reviews/services.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}' \
  | jq '.structured_output.functions'
```
Then look at the whole JSON once, without `jq`:
```bash
claude -p "Say OK" --output-format json | jq 'keys'
```

| Question | Your answer |
|---|---|
| What did `jq` print for `.structured_output.functions`? | |
| Which keys does the JSON output have (look for `result`, `session_id`, `structured_output`)? | |
| Compare the list with `grep -n "^def " reviews/services.py`: does it match? | |
| Why is a schema better than "answer as a list" in the prompt? | |

### Ex 3: Chain two steps with `--resume`

**Where:** Terminal. Use a scratch folder for the files: `/private/tmp/claude-501/-Users-hungle-hungle-training-ai-training/228bfe25-be73-4543-b05b-c59effc97ca6/scratchpad` (or any folder outside the repository).

Step 1, produce a plan and keep the session id:
```bash
claude -p "Plan a minimum rating filter for the reviews page. Do not edit any file." --output-format json > plan.json
jq -r .session_id plan.json
```
Step 2, later, continue the same session:
```bash
claude -p "From your plan, list only the tests I need, one per line." --resume "$(jq -r .session_id plan.json)"
```

| Question | Your answer |
|---|---|
| Did step 2 know the plan without you repeating it? | |
| Where is the session id stored, and does `claude --resume` (interactive) list it too? | |
| When is this pattern better than one long prompt? | |

### Ex 4: `--bare` and what disappears

**Where:** Terminal. Read-only.

Run the same question with and without `--bare`:
```bash
claude -p "List every skill and every hook you know about in this project, by name."
claude --bare -p "List every skill and every hook you know about in this project, by name."
```
`--bare` skips hooks, skills, plugins, MCP servers and CLAUDE.md, and does not use your subscription login (it needs the `ANTHROPIC_API_KEY` environment variable). If the second run asks for a key, **stop**: do not paste a key into a command line or a file. Answer the table from the lesson instead.

| Question | Your answer |
|---|---|
| What did the bare run know about the project? | |
| Did the guard hooks (`.claude/hooks/`) apply in the bare run? | |
| What does that mean for a CI job that runs `claude --bare -p` on this repository? Which protections must you pass in explicitly (`--settings`, `--allowedTools`, `--permission-mode`)? | |
| Which tools stay available in bare mode? (Bash, file read, file edit) | |

### Ex 5: Unattended read-only run with permissions that say no

**Where:** Terminal. Combine this lesson with the permission modes lesson.

```bash
claude -p "Review reviews/services.py for a rounding mistake and report file, line and reason. Do not edit any file." \
  --allowedTools "Read,Grep,Glob" --permission-mode dontAsk --output-format json | jq -r .result
```
Then ask for something outside the allowed tools:
```bash
claude -p "Run the tests and report the result." --allowedTools "Read,Grep,Glob" --permission-mode dontAsk
```

| Question | Your answer |
|---|---|
| Did the second run hang or finish? What did it say? | |
| Which tools would you add to let it run only pytest? (`Bash(uv run pytest:*)`) | |
| Which part of this combination is "the pipeline does not wait for a human"? | |

### Ex 6: Routine or script? (paper exercise)

| # | Job | Routine, headless `-p`, `--bare`, or Agent SDK | Reason |
|---|---|---|---|
| 1 | Every morning at 9am, audit dependencies and open an issue if something is outdated | | |
| 2 | On each new pull request, label it by size and area | | |
| 3 | A script that extracts function names from many files and feeds a database | | |
| 4 | A CI job that must behave the same on every runner and start fast | | |
| 5 | A feature inside your own web product that lets users ask questions about their reviews | | |
| 6 | A nightly plan step and a morning "carry it out" step in your own pipeline | | |

Expected: 1 routine (cron); 2 routine (GitHub event); 3 headless `-p` with `--output-format json --json-schema` and `jq`; 4 `--bare` (needs `ANTHROPIC_API_KEY`); 5 Agent SDK (`query`, `allowedTools`, a permission mode); 6 headless with `--resume` and the session id.

Principle: start with a routine and move down the spectrum only when the job needs more control.

### Ex 7: Design a routine for this project (proposal only)

**Where:** Claude Code, read-only. Do **not** run `/schedule` and do **not** open `claude.ai/code/routines`.

**Prompt:**
```
Design, but do not create, a routine for ReviewRadar that checks every morning whether pyproject.toml and uv.lock have outdated or vulnerable dependencies. Give: the name, the exact prompt (it must say what success looks like and where the result goes, because a routine cannot ask questions), the repository, the trigger (cron expression, and the hourly minimum), the connectors it needs, and what it is allowed to push (a claude/ branch). Then list the risks given .claude/rules/security.md, .claude/rules/git.md and .claude/hooks/github-allowed-repo.txt. Say what limits a routine's push for real (branch protection rules or rulesets) and whether this repository has them today (see the notes on protecting main in docs/learning/epics/working-notes/decision-log.md).
```

| Question | Your answer |
|---|---|
| What does the routine's prompt say counts as "done"? | |
| Where does the result go (issue, pull request, chat)? | |
| Is the push to a `claude/` branch compatible with this repository's rules ("nothing is pushed without approval")? | |
| Does the repository have branch protection today? (the notes say the protection of `main` is blocked by the plan) | |
| Do the guard hooks run in a routine? (find out from the docs before relying on them) | |

Deciding whether to create the routine is a separate task. It needs your approval because it reaches GitHub and Anthropic's cloud.

### Ex 8: When is the result trustworthy? (link to the next lesson)

Write three checks you would require before you trust the output of an unattended `claude -p` run on this repository.

| # | Check | Why it is not enough to read "OK" |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |

(Hint: the exit code of the run, the content of the diff, the result of `ruff`, `mypy` and `pytest` run by a different process, and whether any test file changed.)

## Key takeaways

- **Once Claude does a task reliably, stop running it by hand.** Two ways to hand it off, from least to most control: **routines** (nothing to host) and **headless mode** (your own scripts).
- **Routine = a saved prompt in the cloud.** It bundles a prompt, a repository and any connectors, and runs on Anthropic's infrastructure.
  - Triggers: a **cron schedule** (for example every morning at 9am), an **API** call (an HTTP POST to its endpoint), or **GitHub events** (for example a new pull request).
  - Good for: morning dependency audits, pull request triage, daily scans of an error tracker for urgent items.
  - Create it on `claude.ai/code/routines` or in the terminal with `/schedule daily dependency audit at 9am`.
  - Limits: research preview; a recurring schedule runs at most **hourly**; each run starts from a **fresh clone of the default branch** and pushes to a `claude/` branch unless the prompt names another; on pull request events the run starts from the pull request's head commit. To control pushes use **GitHub branch protection rules or rulesets**: a rule the connected access can bypass blocks nothing.
- **Headless = `claude -p`** (`--print`): a one-shot, non-interactive run that reads stdin, writes stdout and pipes like a shell tool. On its own it loads hooks, skills, plugins, MCP servers and CLAUDE.md.
  - **Structured output:** `--output-format json` with `--json-schema`; the object appears in `structured_output`, which you read with `jq`.
  - **Multi-step:** keep the `session_id` from the JSON and continue later with `--resume`.
  - **`--bare`:** skips auto-discovery of hooks, skills, plugins, MCP servers and CLAUDE.md; keeps the Bash, file read and file edit tools; config is passed explicitly (`--settings`, `--mcp-config`). Same setup on every machine and faster start. It does not use the subscription login: set `ANTHROPIC_API_KEY`.
- **Agent SDK:** embeds Claude Code in your own TypeScript or Python application with a `query` function; options include `allowedTools`, a system prompt and a permission mode; you handle the streamed messages.
- **Decision guide:** routines for repeat work; `-p` when you need your pipeline and piped data; `--bare` for consistent CI; Agent SDK when the work belongs inside your product. Start with routines and move down only when needed.
