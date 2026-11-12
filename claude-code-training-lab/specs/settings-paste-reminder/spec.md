# Spec: settings-paste-reminder

## Summary

`ops/release.py` prints one more line, in the dry run and in the real release, when `.claude/project-instructions.md` on the released commit differs from the last release (`origin/deploy`). After that line the release thread gives the owner the whole file to paste into the Project settings. Nothing visible to users of the app.

## User story

As the owner, I want to know when the Project settings no longer match `.claude/project-instructions.md`, so that threads follow the rules that are on `main`.

## Acceptance criteria

- **AC1.** Given `origin/deploy` at commit A and `origin/main` at commit B where `.claude/project-instructions.md` differs between A and B, when `release.py --dry-run` runs, then the last line of the plan, after `Internal pull requests:` and its lines, is exactly `Project settings: .claude/project-instructions.md changed since the last release; paste it into Project settings.` The real release prints the same line at the same place (the deploy line, when there is one, stays after it).
- **AC2.** When the file is the same at A and B, or does not exist at B, the line is not printed and the output is exactly as on `main`.
- **AC3.** First release (no `origin/deploy`): the line is printed when the file exists at B.
- **AC4.** The check reads only git objects of the fetched commits (no working tree, no network beyond the existing fetch). If the git command of the check fails, the line is not printed and the release goes on (no refusal, exit code unchanged).
- **AC5.** `release.Plan` gets a new field with a default, so a `Plan` built without it (as in `ops/tests/test_release_security.py`) keeps working. New tests in `ops/tests/test_release_settings_reminder.py` (fixture repositories as in `ops/tests/test_release.py`, no network) cover AC1 to AC4 for the dry run and the real release. `ops/README.md`, section Release, names the line. Every test on `main` passes unchanged (their fixtures have no `.claude/` folder, AC2).
- **AC6.** `.claude/project-instructions.md`, Release paragraph: when the `release.py` output has the `Project settings:` line, after the release report the thread posts the whole file from `main` in one code block, saying "Paste this into Project settings (replace all)". After the merge the thread gives the owner the new Release paragraph to paste.

## Edge cases

- Empty: file missing on the released commit: no line.
- Large data: the file is about 10 KB; one code block.
- Permissions: none beyond the release.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 How to notice drift? | `release.py` prints a reminder when the file changed since the last release; the thread gives the text to paste | A checksum line in the Project settings that every thread compares; both | Tested code at the moment the owner already acts, and one paste per release (owner, 2026-11-12) |
| Where the line goes | The last line of the plan (dry run and real release), before the deploy line | Before the commit line | The deploy line stays last; the owner reads it on the release card |
| The path | A constant in `ops/release.py` | A key in `ops/flow.toml` | `ops/flow_config.py` and `ops/flow.toml` are changed by the post-release epic; no other project uses the line yet |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
