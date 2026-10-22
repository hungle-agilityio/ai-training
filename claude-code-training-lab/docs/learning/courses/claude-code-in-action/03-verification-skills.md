# Lesson 3: Verification skills

- **Course:** Claude Code in action (lesson 3 of 9, ~5 min)
- **Source:** https://academy.claude.com/courses/claude-code-in-action/verification-skills
- **Date:** 2026-10-20
- **Status:** In progress

The lesson has no exercises of its own. These exercises are written for this lab and use the verification skills ReviewRadar already has (`/verify`, `build-verify-report`, `check-in-browser`). Run them in Claude Code, folder `claude-code-training-lab`. They read, run checks and propose; do not edit `.claude/` or commit. Revert anything by accident with `git checkout .` (and `git clean -n` to see new files first).

## Exercises

### Ex 1: Read the verification skill like a recipe

**Where:** Claude Code, read-only.

**Initial prompt:**
```
what does /verify do?
```

**Improved prompt:**
```
Read .claude/commands/verify.md and .claude/skills/build-verify-report/SKILL.md. Compare them with this checklist of a good verification skill: (1) fires on its own from its description, (2) runs the test suite, (3) reads the diff, (4) checks that no test was weakened to make things pass, (5) reports pass or fail with the evidence attached. For each item say yes, partly or no, with the line that shows it. Do not edit any file.
```

| # | Checklist item | Yes / partly / no | Where in the skill |
|---|---|---|---|
| 1 | Fires from its description | | |
| 2 | Runs the tests | | |
| 3 | Reads the diff | | |
| 4 | Checks that no test was weakened | | |
| 5 | Reports with evidence | | |

**Check:** the lesson says green tests alone are not enough. Write in one line what "weakened" means here (for example a deleted assertion, a loosened expected value, a skipped or removed test).

### Ex 2: "Done is the gates being run and observed"

**Where:** Claude Code, permission mode **Accept edits**. Revert afterwards.

**Initial prompt:**
```
refactor reviews/services.py and tell me when it is done
```

**Improved prompt:**
```
Refactor one function in reviews/services.py without changing its behaviour. When you finish, run the gates yourself and state the result of each one explicitly: uv run ruff check . ; uv run mypy . ; uv run pytest -q --no-cov. Print the last lines of each output. Then read the diff and tell me whether any test file changed. Do not say "done" without those results.
```

| Gate | Command | Result stated by Claude | Output shown? |
|---|---|---|---|
| Lint | `uv run ruff check .` | | |
| Types | `uv run mypy .` | | |
| Tests | `uv run pytest -q --no-cov` | | |
| Test files changed? | `git diff --stat reviews/tests` | | |

### Ex 3: Plant a weakened test and see if the skill notices

**Where:** Claude Code. Revert afterwards.

This is the gap the lesson names. Test whether your own verification catches it.

1. Make a small, deliberate break in the rule (for example change the rounding in `rounded_average` so one test fails).
2. Instead of fixing the code, weaken the test: loosen the expected value or delete one assertion.
3. Run:
```
/verify
```
(or the verify command with a criteria file, as the skill asks).
4. Read the report: does it mention the test change anywhere?

| Question | Your answer |
|---|---|
| Did the report say PASS while a test was weakened? | |
| Which axis could have caught it (tests, coverage, review)? | |
| Would the `reviewer` sub-agent have caught it? (run `/review` on the diff to see) | |

Then ask for a **proposal only**:
```
Propose a "weakened tests" check for the build-verify-report skill: what it looks at in git diff (removed assertions, changed expected values, new skip or xfail marks, deleted test files), what it reports and how it fails. Show it as a short list of rules. Do not edit any file.
```
Choosing whether to add it is a separate task with its own plan.

### Ex 4: What belongs in side files?

**Where:** Claude Code, read-only.

**Prompt:**
```
For each skill in .claude/skills, tell me: how many lines is SKILL.md, which side files it has (reference or checklist files, scripts, tests), and whether the heavy detail lives in the side files or in SKILL.md. Output a table and name the skill whose SKILL.md is longest.
```

| Skill | SKILL.md lines | Side files | Lean SKILL.md? |
|---|---|---|---|
| `build-verify-report` | | | |
| `check-in-browser` | | | |
| `share-report` | | | |
| `grill-me` | | | |
| `create-commit` | | | |
| The longest one | | | |

| Question | Your answer |
|---|---|
| Which script does Claude execute instead of reading it into context? | |
| Which file holds depth read only when needed (like `reference.md`)? | |
| Is any SKILL.md long enough that part of it should move to a side file? | |

### Ex 5: The "typed it twice" test

**Where:** Paper, then Claude Code to check.

Rule of thumb from the lesson: if you typed the same multi-step instruction twice, that is a skill.

1. Open the last days of the journal (`docs/learning/journal/`) and your recent prompts.
2. List two or three multi-step instructions you gave more than once in these lessons (for example "run ruff, mypy and pytest and show the output", or "revert with `git checkout .` and check `git clean -n`").
3. Ask:
```
Which of these repeated instructions are already covered by a skill or command in .claude/? Name the file. For the ones that are not, propose a skill name (verb plus object, at most 3 words, per .claude/rules/naming.md) and a one-line description that says what it does and when to use it. Do not create any file.
```

| Repeated instruction | Already covered by | Proposed skill name |
|---|---|---|
| | | |
| | | |
| | | |

### Ex 6: Run one verification end to end

**Where:** Claude Code, folder `claude-code-training-lab`.

Run the build on the current clean tree (no change needed):
```
uv run python .claude/skills/build-verify-report/build_report.py --title "Lesson 3 check" --criteria <a criteria file> --no-open
```
If you have no criteria file, ask Claude to write one with a single `NOT CONFIGURED` entry and say why. Then open `out/verify/<time>/report.html` and read every axis.

| Axis | Result | Evidence shown? |
|---|---|---|
| Lint | | |
| Types | | |
| Tests | | |
| Coverage | | |
| Skill and hook tests | | |
| Issue criteria | | |
| Query count | | |
| Security | | |
| Browser | | |

| Question | Your answer |
|---|---|
| Is there any axis with PASS and no evidence? | |
| What does the report say when an axis cannot be checked? (expected: `NOT CONFIGURED` and why) | |

### Ex 7: Which surface owns which rule (paper exercise)

| # | Rule | CLAUDE.md, skill or hook | Reason |
|---|---|---|---|
| 1 | Services contain no HTTP objects | | |
| 2 | After a refactor, run the tests, read the diff, check no test was weakened, report with evidence | | |
| 3 | No commit message may contain a `Co-Authored-By` line | | |
| 4 | Pre-pull-request checklist: issue number, evidence, one concern | | |
| 5 | Never print the token | | |
| 6 | New files go in `reviews/`, one view per module | | |

Expected: 1 CLAUDE.md (a convention that always applies); 2 skill (a procedure for a kind of task); 3 hook (must not be skippable; the commit hook already checks it); 4 skill (`draft-pull-request`); 5 hook; 6 CLAUDE.md.

## Key takeaways

- **Build the verification skill first.** Checking Claude's work should not depend on you remembering to ask. The skill fires on its own from its description and: runs the test suite, reads the diff, checks that no test was weakened to make things pass, and reports pass or fail with the evidence attached.
- **Green tests alone are not enough.** "Done is the gates being run and observed, with the results stated explicitly."
- **The same idea fits** release checklists, migration recipes and pre-pull-request checks. **Rule of thumb:** if you typed the same multi-step instruction twice, make it a skill.
- **A skill folder holds more than instructions.** A `reference.md` beside `SKILL.md` (read only when Claude needs that depth) and scripts such as `check.sh` (executed, not loaded into context). Keep `SKILL.md` lean: it says what to do; side files hold the depth and the tools.
- **Which surface owns which rule:**

| Surface | Use for |
|---|---|
| `CLAUDE.md` | Conventions that always apply (naming, where files go) |
| Skills | Procedures and reference for a particular kind of task |
| Hooks | Rules Claude must not be able to skip |

- A hook is code that actually runs. CLAUDE.md and skills are instructions Claude follows, so if skipping a rule is not acceptable, do not rely on instruction-following.
- **Recap:** a skill is a folder with `SKILL.md` (a name, a triggering description, the procedure). Only the descriptions are in context until a skill is needed, so packaging every repeated procedure costs little. Check the verification skill into `.claude/skills` and the whole team inherits the same checks.
