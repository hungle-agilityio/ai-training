---
name: draft-pull-request
description: Draft a pull request from the evidence (verify report, before and after images, issue number) and say whether it is complete. Writes the description and a local folder of masked images to drag in. Use before create-pull-request, or when the user asks for a pull request draft.
---

# Draft a pull request

The draft is built from real evidence, not from memory. Nothing is created on GitHub here; `create-pull-request` does that after the user approves the preview.

## Run it

```
uv run python .claude/skills/draft-pull-request/draft_pr.py --title "[FEAT] ..." --what "..." --why "..." \
  [--issue N] --report out/verify/<folder> (--compare out/before-after/<folder> | --no-visual) [--out DIR]
```

Output (default `out/pr-draft/<branch>/`, git-ignored): `pr-body.md`, `images/` and `draft.json`.

## What it checks

| Check | Result when it fails |
|---|---|
| Title starts with `[BUG]`, `[FEAT]`, `[TASK]` or `[EPIC]` | incomplete |
| What and Why are not empty | incomplete |
| A verify report is given, and its verdict is PASS | incomplete (a FAIL is still written honestly in the body) |
| Before and after images are given and their masking is `clean`, or `--no-visual` | incomplete; unmasked images are never copied |
| An issue number | complete but `ready_to_create: false`; the body says "no issue number yet" and has no `Closes` line |

## Rules

- Only pages labelled `changed` or `did not exist before` are copied to `images/`; "no visible difference" is left out.
- The report link is the private artifact link when the report was shared, else "not shared" with the local path.
- Never invent an issue number. Create the issue first (`create-issue`), then run the draft again with `--issue`.
- Images are dragged into the pull request by the user from `images/`; the description names the files.
