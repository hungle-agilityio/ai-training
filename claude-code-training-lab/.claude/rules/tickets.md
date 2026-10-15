---
paths:
  - "docs/issues/**"
  - "docs/templates/**"
  - ".gitlab/**"
---

# Ticket rules

Use the skill `write-ticket` (bug, feature or task) to create tickets.

- **Ticket ID:** the GitLab issue number (IID), assigned when the issue is published, written `#6` in text. A draft ticket has no ID yet. The type is shown by the title (`[BUG]`) and by the branch prefix, never by the ID.
- **Title format:** `[type] title`, where type is `BUG`, `FEAT` or `TASK`. Example: `[BUG] dashboard show wrong score number`. The ticket number is not part of the title or the folder name.
- **Folders:** issues live in `docs/issues/`, grouped by type (`bugs/`, `features/`, `tasks/`). Each issue is a folder named after it, for example `docs/issues/bugs/dashboard-wrong-score/`, where the name is the short lowercase description also used in the branch name (`bug/1-dashboard-wrong-score`).
- **Index:** `docs/issues/README.md` lists local number, GitLab issue, type, folder and title; add a row for every new issue.
- **Tone:** tickets are written in plain language for QA, BA and clients: no code, commits, branches or technical terms.
- **`04-final.md`:** the only file `write-ticket` creates. It is the complete standalone ticket, built from `docs/templates/04-final-bug.md`, `04-final-feature.md` or `04-final-task.md`, and posted as a GitLab issue, so it must not refer to any other file.
- **`01-reported.md`, `02-analysis.md`, `03-discussion.md`** (templates in `docs/templates/`) are learning material: the report as received, our analysis and questions, and the conversation with the reporter. The skill does not create or change them.
- **Markdown placeholders:** write `\<placeholder>`, not `<placeholder>`; the preview treats bare angle brackets as HTML and hides them.
