# Test matrix: settings-paste-reminder

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | File changed since `origin/deploy`: the dry run ends with the `Project settings:` line. | integration | `ops/tests/test_release_settings_reminder.py` | T1 |
| M2 | AC1 | normal | Real release: the line comes after the pull request groups and before the deploy line. | integration | `ops/tests/test_release_settings_reminder.py` | T1 |
| M3 | AC2 | edge | File unchanged, or missing on the released commit: no line, output as on `main`. | integration | `ops/tests/test_release_settings_reminder.py` | T1 |
| M4 | AC3 | edge | No `origin/deploy` and the file exists: the line is printed. | integration | `ops/tests/test_release_settings_reminder.py` | T1 |
| M5 | AC4 | error | The git command of the check fails: no line, exit code as without the check. | integration | `ops/tests/test_release_settings_reminder.py` | T1 |
| M6 | AC5 | normal | A `Plan` without the new field keeps working; `ops/README.md` names the line. | unit | `ops/tests/test_release_settings_reminder.py` | T1 |
| M7 | AC6 | normal | After a release that changed the file, the thread posts the whole file to paste. | manual | Ask "phát hành", choose A, read the thread. | T2 |
