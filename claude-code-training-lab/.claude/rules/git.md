# Git and GitLab rules

The step-by-step procedure is in the skills `create-commit`, `create-issue` and `create-pull-request`. This file is only the format.

## Hard rules

- Never commit directly to `main`. One branch per ticket.
- Nothing is pushed, published or created on GitLab without the user's approval for that item.
- Claude never merges or approves a merge request.
- No `Co-Authored-By` or "Generated with" line in commits.

## Branches

- Format: `<kind>/<id>-<short-description>`, the ticket number and a short lowercase description separated by dashes.
  - Bug: `bug/1-dashboard-wrong-score`
  - Feature: `feat/4-filter-reviews`
  - Task: `task/6-cleanup-demo-data`
- The branch needs the issue number, so publish the ticket first.

## Commits

Three parts separated by a blank line:

```
<title>

<detail>

Part of <id>
```

- **title:** short, imperative, says what changed (no ticket ID).
- **detail:** what changed and why, lines wrapped at about 72 characters.
- **Part of `<id>`:** the ticket ID, for example `Part of #1`; one line per ticket if a commit touches several.

Example:

```
Fix average score rounding on dashboard

The average was calculated with whole-number division, so 11 / 3
showed as 3. It now keeps the decimals (3.67).

Part of #1
```

## GitLab and merge requests

- Remote: GitLab `https://gitlab.asoft-python.com`, project `hung.le/ai-training`. Issues and merge requests are created through the GitLab MCP server with the skills `create-issue` and `create-pull-request`.
- A ticket is drafted and reviewed locally, and published as a GitLab issue only after the user approves it (type, labels, assignee `hung.le`). The skill reports `title | link`.
- Merge request: into `main`, title `[type] title` (for example `[BUG] dashboard show wrong score number`), description from `.gitlab/merge_request_templates/Default.md`, ending with `Closes #<number>`. Created only after the user approves the preview.
