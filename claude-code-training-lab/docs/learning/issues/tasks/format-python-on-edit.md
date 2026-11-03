# [TASK] Format a Python file each time Claude edits it

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-11-03
- **Type:** Task
- **Labels:** `task`, `tooling`, `agent:manual`

## Summary

When Claude edits or writes a Python file, the import order and the layout are fixed by hand or left for the lint step to complain about. A hook that runs after every edit of a `.py` file fixes them at once, so the diff Claude shows is already clean and the lint check at commit time has less to refuse. It touches only the Claude Code setup (`.claude/hooks/`, `.claude/settings.json`); nothing visible to users.

## Scope

- **Included:** a new hook `after-edit-format` that runs after Edit and Write on a `.py` file inside the project: `ruff check --fix` then `ruff format` on that one file; its entry in `.claude/settings.json`; its tests in `.claude/hooks/tests/`; one row in `.claude/hooks/README.md`.
- **Not included:** reformatting the 22 files that are not formatted today (each is formatted the first time it is edited); formatting other languages; adding a `ruff format --check` step to the automatic checks.

## Done when

- [ ] When Claude edits a Python file with unsorted imports, the file must have its imports sorted right after the edit.
- [ ] When Claude edits a Python file with bad layout (for example a missing blank line between functions), the file must be laid out as `ruff format` lays it out.
- [ ] When Claude edits a file that is not Python (Markdown, HTML, JSON), the file must be left exactly as Claude wrote it.
- [ ] When `ruff` cannot read the file (a syntax error), the edit must be kept and Claude must see one line saying the file was not formatted; the edit is never undone.
- [ ] When the hook tests run in the automatic checks, they must pass.

## Steps to check the result

1. Open a new Claude Code session in `claude-code-training-lab/`.
2. Ask Claude to add `import os` at the top of `reviews/forms.py`, above the existing imports.
3. Open `reviews/forms.py`.

## Expected result

`import os` is in its sorted place among the imports (or removed if unused is reported), and `git diff` shows no other change than the import line and layout fixes.

## Environment

dev (Claude Code on the owner's Mac and the Mac mini)

## Attachments

Hook naming follows `rules/naming.md` (`<when>-<purpose>`). Exercise: "Hooks and automation, ship one as a PR".
