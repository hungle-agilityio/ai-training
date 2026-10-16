---
paths:
  - "docs/app/issues/**"
  - "docs/app/templates/**"
  - "docs/learning/issues/**"
  - ".gitlab/**"
---

# Ticket rules

Use the skill `write-issue` (bug, feature or task) to create tickets.

- **Ticket ID:** the GitLab issue number (IID), assigned when the issue is published, written `#6` in text. A draft ticket has no ID yet. The type is shown by the title (`[BUG]`) and by the branch prefix, never by the ID.
- **Title format:** `[type] title`, where type is `BUG`, `FEAT` or `TASK`. Example: `[BUG] dashboard show wrong score number`. The ticket number is not part of the title or the file name.
- **Files:** issues are grouped by type (`bugs/`, `features/`, `tasks/`). **One issue is one markdown file** named after it, for example `bugs/dashboard-wrong-score.md`, where the name is the short lowercase description also used in the branch name (`bug/1-dashboard-wrong-score`). Two roots: `docs/app/issues/` for issues of the app, `docs/learning/issues/` for work on how we use Claude Code (the epic in `docs/learning/epics/`). Epics are single files in `docs/learning/epics/`. Issues made before 2026-10-16 keep their four-file folders (learning exercise); do not copy that layout.
- **Index:** `docs/app/issues/README.md` and `docs/learning/issues/README.md` list local number, GitLab issue, type, file and title; add a row for every new issue.
- **Tone:** tickets are written in plain language for QA, BA and clients: no code, commits, branches or technical terms.
- **The issue file:** the only file `write-issue` creates. It is the complete standalone issue, built from `docs/app/templates/04-final-bug.md`, `04-final-feature.md` or `04-final-task.md`, and posted as a GitLab issue, so it must not refer to any other file.
- **Old four-file folders** (`01-reported.md`, `02-analysis.md`, `03-discussion.md`, `04-final.md`) are learning material from the training: the report as received, our analysis, the conversation and the final issue. Do not create or change them.
- **Markdown placeholders:** write `\<placeholder>`, not `<placeholder>`; the preview treats bare angle brackets as HTML and hides them.
