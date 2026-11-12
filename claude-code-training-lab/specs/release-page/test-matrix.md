# Test matrix: release-page

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | With `--notes-url`, the notes file has the exact text of AC1 and `gh release create v<tag> --title v<tag> --notes-file <file> --verify-tag` runs. | integration | `ops/tests/test_release_github_page.py` | T1 |
| M2 | AC1 | empty | Without `--notes-url` no link lines; an empty group says `- (none)`. | integration | `ops/tests/test_release_github_page.py` | T1 |
| M3 | AC2 | normal | stdout starts with `Release page: <url>` and ends with the deploy line. | integration | `ops/tests/test_release_github_page.py` | T1 |
| M4 | AC3 | error | `gh` exit 1, `OSError`, timeout: exit 0, the warning line on stderr, no second push. | integration | `ops/tests/test_release_github_page.py` | T1 |
| M5 | AC4 | edge | Local-path `origin`: no file, no `gh release create`; `--dry-run`: no file, no `gh release create`. | integration | `ops/tests/test_release_github_page.py` | T1 |
| M6 | AC5 | normal | `ops/README.md` names `--notes-url` and the Release page. | unit | `ops/tests/test_release_github_page.py` | T1 |
| M7 | AC6 | normal | After the next release the thread reports the `Release page:` line. | manual | Ask "phát hành", choose A, read the thread and open the Release. | T2 |
