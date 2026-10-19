# Skills base

How every skill in this folder is built, so a new one can be written the same way. Names follow `rules/naming.md` (verb + object, kebab-case, at most 3 words, no tool names).

## Layout of a skill

```
.claude/skills/<verb-object>/
  SKILL.md        the procedure: frontmatter (name = folder name, description saying what and when), then the steps
  <program>.py    only when a step must be exact (a checker, a builder); the rule it applies is in the rulebook
  rules.md        the rulebook, when a program reads rules that people change (for example share-report)
  checklist.md    reference material the procedure points to (for example grill-me)
  tests/          pytest tests of the program, with one sample input and the expected output
```

## Rulebook files: where they live

- Rules that a program reads sit **next to it** in the skill folder (`share-report/rules.md`), so changing a rule is one small diff.
- Rules every skill must follow sit in `.claude/rules/` and are not copied into skills.
- A skill never repeats a rule from `rules/`; it names the file.

## Test pattern

- A skill with a program has `tests/test_<program>.py`: one small sample input in, the expected output asserted, and one case per refusal the program makes. Tests run in CI (`uv run pytest .claude/hooks/tests .claude/skills`).
- A skill without a program is a procedure for Claude. It has no test of its own; its worked example is the run recorded in the journal or in a verify report, and the reason is written in the table below.
- `.claude/skills/tests/test_skill_layout.py` checks the layout of every skill (name = folder, naming rule, a description, a program has tests).

## The skills

| Skill | Program | Tests | Example run |
|---|---|---|---|
| `build-verify-report` | `build_report.py` | yes | `/verify` on any change |
| `capture-before-after` | `before_after.py` | yes | `--base <ref>` on a branch |
| `check-in-browser` | `browser_check.py` | yes | `--plant` stops the run (exit 3) |
| `create-issue` | `check_issue.py` | yes | the checker on an issue file |
| `draft-pull-request` | `draft_pr.py` | yes | a draft from a verify report and a before and after run |
| `share-report` | `share_gate.py` | yes | the gate on a report folder |
| `create-commit`, `create-pull-request`, `diagnose-bug`, `grill-me`, `review-pull-request`, `write-issue`, `write-tests` | none | no | Procedures for Claude, with no exact computation to test; `create-commit` and `create-pull-request` are also guarded by the hooks (`.claude/hooks/tests`), `write-issue` by `check_issue.py` |
