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
- `.claude/skills/tests/test_skill_layout.py` checks the layout of every skill (name = folder, naming rule, a description, a program has tests).

A skill without a program is a procedure for Claude and has no test of its own. Which skills have a program: look for `*.py` in the folder.
