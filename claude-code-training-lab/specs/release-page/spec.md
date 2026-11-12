# Spec: release-page

## Summary

After `ops/release.py` pushes the release, it creates a GitHub Release for the new tag with `gh release create`, whose notes are the release's pull request groups and, when given, a link to the release notes page. A failure to create the page is a warning, not a failed release. Nothing visible to users of the app.

## User story

As the owner, I want each release tag to have a GitHub Release page with its pull request list and a link to the release notes, so that clients and the team see what shipped in one place.

## Acceptance criteria

- **AC1.** `ops/release.py` takes an optional `--notes-url <url>`. Given a release of tag `v2026.11.12` on `release/sprint-6` at commit `5b8d883` with client-facing `#525 A member's claimed task holds its files in the loop` and internal `#528 spec: epic-review-checklist`, when `release.py --notes-url https://claude.ai/artifact/9YeTDzCKwuvkYq2jDphaye` has pushed, then it writes `<loop.state_dir>/release-v2026.11.12.md` with exactly:

  ```
  Release v2026.11.12 (release/sprint-6, commit 5b8d883)

  Client-facing pull requests:
  - #525 A member's claimed task holds its files in the loop

  Internal pull requests:
  - #528 spec: epic-review-checklist

  Release notes: https://claude.ai/artifact/9YeTDzCKwuvkYq2jDphaye
  ```

  (a group with no pull request says `- (none)`; without `--notes-url` the last line and the blank line before it are left out), and runs `gh release create v2026.11.12 --title v2026.11.12 --notes-file <that file> --verify-tag` in the repository.
- **AC2.** On success, stdout starts with `Release page: <url printed by gh>` and then the lines of `main` (`Commit:`, `Branch:`, `Tag:`, the security lines, the two groups, the deploy line last), so the deploy line stays the last line.
- **AC3.** When `gh release create` fails or cannot run (non-zero exit, `OSError`, a 60-second timeout), `release.py` still exits 0 and prints the lines of `main`; stderr gets one line `warning: GitHub Release not created (<last line of gh's error, or the error name>); run: gh release create <tag> --title <tag> --notes-file <file> --verify-tag`. The tag, the branch and `deploy` are not touched again.
- **AC4.** When the `origin` remote of the repository is not a GitHub URL (it does not contain `github.com`), no notes file is written, `gh release create` is not run and nothing more is printed. `--dry-run` never writes the file nor runs `gh release create`; it prints the plan as on `main`.
- **AC5.** New tests in `ops/tests/test_release_github_page.py` (a fake `gh` through a patched `subprocess.run`, a fixture repository whose `origin` URL is set to `https://github.com/acme/shop.git` for the GitHub cases; no network): the notes file of AC1 with and without `--notes-url` and with an empty group; the command of AC1; the stdout order of AC2; each failure of AC3 with exit 0 and the warning; the skip of AC4 and the dry run. `ops/README.md` names `--notes-url` and the Release page in its release section. Every test on `main` passes unchanged (their fixture remotes are local paths, AC4).
- **AC6.** `.claude/project-instructions.md`, Release paragraph: the release command becomes `uv run python ops/release.py --notes-url https://claude.ai/artifact/9YeTDzCKwuvkYq2jDphaye`, and the thread reports the `Release page:` line, or the warning of AC3 with its command. After the merge the thread gives the owner the paragraph to paste into Project settings.

## Edge cases

- Empty: a release with no pull request in a group: `- (none)` under that group.
- Large data: no limit on lines; the file is plain text.
- Permissions: `gh` uses the owner's login on the Mac mini, which may create releases on the repository; a 403 is the warning of AC3.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 What does the Release page say? | The pull request groups of the release and a link to the release notes page | Extra client text written by the thread | The notes page already has the client text; no manual step per release (owner, 2026-11-12) |
| Q2 Release page fails after the push | A warning with the command to retry; the release exits 0 | Exit 1 | The release is already live; the page is a record (owner, 2026-11-12) |
| Where the notes link comes from | A `--notes-url` option the release thread passes | A new `[release]` key in `flow.toml` | `ops/flow_config.py` and `ops/flow.toml` are changed by the post-release epic; an option needs no config change |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
