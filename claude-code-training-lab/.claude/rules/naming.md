# Naming rules

One pattern for every name in `.claude/`, so a new name can be guessed. Decided in epic problem P01; renames are applied in P02 to P04.

## Pattern

| Thing | Pattern | Examples |
|---|---|---|
| Skill | `verb-object`, imperative, lowercase kebab-case, at most 3 words, one job each | `write-issue`, `create-commit`, `review-pull-request` |
| Command | one lifecycle verb, in workflow order | `/understand`, `/plan`, `/implement`, `/test`, `/review`, `/verify`, `/learn`, `/commit` |
| Sub-agent | the role, as a noun (`analyst`, `planner`, `implementer`, `reviewer`, `test-runner`); the description states its role (advisor, builder, runner) | `analyst`, `test-runner` |
| Sub-agent model | short alias (`opus`, `sonnet`, `haiku`), never a pinned version | `model: sonnet` |
| Hook | `<when>-<purpose>` | `before-commit-check` |
| Rule, context, knowledge file | the topic, as a noun | `security.md`, `domain.md` |

## Never in a name

- A platform or tool (`github`, `gitlab`, `git`, `claude`): the host can change, the job stays.
- A vague word (`helper`, `utils`, `misc`).
- A ticket number.

## Words

- Say **issue** (not "ticket") and **pull request** (not "merge request"). Issues are grouped as bug, feature or task.
- Names and text in the project are English.

## Planned renames

| Now | New | Problem |
|---|---|---|
| skill `debug` | `diagnose-bug` | P02 |
| skill `git` | `create-commit` | P02 |
| skill `gitlab` | `create-issue` and `create-pull-request` | P02 |
| skill `pr-review` | `review-pull-request` | P02 |
| skill `testing` | `write-tests` | P02 |
| skill `write-ticket` | `write-issue` | P02 |
| agent `ticket-analyst` | `analyst` | P03 |
| agent `ticket-planner` | `planner` | P03 |
| agents `implementer`, `reviewer` | keep | P03 |
| new | `test-runner` (P17); `grill-me` (P14, done) | P17 |
