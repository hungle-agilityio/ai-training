# Spec: release-deploy

## Summary

Render stops following `main` and follows one branch, `deploy`, that only moves when the owner makes a release. A release is made by `ops/release.py` on the Mac mini, after the owner presses a card in the Project. It takes the newest commit on `main` whose `Checks` are green, creates the branch `release/sprint-N` and the tag `vYYYY.MM.DD` on it, and fast-forwards `deploy` to it, in one push without force. Render then deploys that commit after its checks pass (the commit is the same one `main` checked, so no new CI run is needed). Nothing changes in the app's pages. This replaces AC8 (branch), AC11 (deploy text), AC13 and decision Q3 of `specs/auto-deploy/spec.md`.

## Acceptance criteria

Render and README (issue #65, pull request #101, changed by a comment):

- **AC1.** `render.yaml` has `branch: deploy` and keeps `autoDeployTrigger: checksPass`; every other value stays as in auto-deploy AC8 to AC10.
- **AC2.** `reviews/tests/integration/test_render_blueprint.py` expects `branch` to be `deploy`.
- **AC3.** The README "Deploy" section says: a merge to `main` does not change the live site; a release does (branch `release/sprint-N`, tag `vYYYY.MM.DD`, branch `deploy` that Render follows); the owner asks for a release in the Project; a bad release is undone with Render's Rollback button and then fixed on `main` with a new release. Its one-time steps say the first release must be made before the Blueprint is created, because Render needs the `deploy` branch to exist.

Release script (`ops/release.py`):

- **AC4.** `uv run python ops/release.py --dry-run` fetches `origin`, then prints the `main` commit it would release (short sha and title), the next branch name, the tag, and the merged pull requests since the last release (`#N title`, one per line, read from the merge commits on `main` between `origin/deploy` and that commit; all merges when `deploy` does not exist yet). It pushes nothing and exits 0.
- **AC5.** It refuses, exits 1 with one line saying why, and pushes nothing when: the newest `Checks` workflow run for the `main` commit is missing, still running, or did not succeed; `origin/deploy` already points at that commit ("nothing new to release"); or `origin/deploy` is not an ancestor of that commit.
- **AC6.** The branch is `release/sprint-N`, where N is one more than the highest N among the `release/sprint-*` branches on `origin`, or 1 when there is none.
- **AC7.** The tag is an annotated tag `v<YYYY.MM.DD>` with the date in Vietnam time (`Asia/Ho_Chi_Minh`); when that tag exists, `.2`, then `.3` and so on is added. The tag message is the branch name.
- **AC8.** Without `--dry-run`, after the same checks, it runs one `git push --atomic origin` that creates the branch, creates the tag and moves (or, on the first release, creates) `deploy`, all on that commit. It never uses `--force`, `+` refspecs or `--delete`, never pushes `main`, and never changes an existing `release/sprint-*` branch or tag.
- **AC9.** After a successful push it prints the branch, the tag, the commit and the pull request list of AC4, and the line `Render deploys branch deploy after Checks pass.`
- **AC10.** Tests in a new file `ops/tests/test_release.py` cover AC4 to AC9 with a temporary bare git repository as `origin` and a fake for the `Checks` lookup; they do not use the network.
- **AC11.** `ops/README.md` has a "Release" section: what the script does, `--dry-run`, and the refusals of AC5.

Flow (`.claude/`, done by hand):

- **AC12.** ADR-017 records: deploys go out only by release; the branch names `release/sprint-N` and `deploy`; only `ops/release.py` pushes them, fast-forward only, never force; the loop and Claude builds never push them; rollback through Render, then a fix on `main` and a new release; it replaces auto-deploy decision Q3.
- **AC13.** `.claude/project-instructions.md` has a Project command "phát hành": a thread on the Mac mini runs `uv run python ops/release.py --dry-run` in the main checkout, shows its output on a choice card (A "Phát hành (đề xuất)", B "Huỷ"), runs `uv run python ops/release.py` after A, and reports the branch, the tag, the pull request list and a refusal reason if any. The owner pastes the new text into the Project's instructions.
- **AC14.** `.claude/CLAUDE.md` "Removed, and why" has a row for "Deploy on every green merge to `main`" with today's date, the reason (the owner wants a release per sprint) and "Rebuild from" ADR-017.

Live result, checked by the owner:

- **AC15.** After the Blueprint is created from the `deploy` branch, merging a pull request into `main` starts no deploy on Render.
- **AC16.** After a release, Render's deploy list shows the released commit, deployed once its checks passed; the site shows that version.

## Edge cases

- First release: `deploy` does not exist; it is created on the released commit, N is 1, and the list holds every merged pull request.
- Two releases on one day: the second tag is `vYYYY.MM.DD.2`; the branch is the next sprint number.
- No new merge since the last release: refused, "nothing new to release".
- `main` red or still running: refused; the owner waits for green and presses the card again.
- After a Render Rollback: `deploy` still points at the bad release; the fix is merged into `main` and the next release fast-forwards `deploy` as usual.
- Permissions: only the owner's Mac mini, with the owner's login, makes a release; the loop never runs the script.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Release branch | One branch per sprint, `release/sprint-N` | One fixed `release` branch | The owner wants each sprint kept as its own branch. |
| Q2 How a release is cut | Card in the Project, Mac mini runs `ops/release.py` | Pull request from `main` into `release`; owner pushes by hand | No typing; the released commit is the one `main` already checked, so no `.github/` change. |
| Q3 Tag | Date tag `vYYYY.MM.DD`, `.2` for a second one that day | Semver; no tag | No version number to choose; easy to read. |
| Q4 Protection | Written rule in ADR-017 | GitHub ruleset | No extra manual step for the owner now. |
| Q5 Rollback | Render Rollback, then fix on `main` and release again | Move the branch back to an old tag | Moving back needs a force push, which the project never does. |
| Q6 PR #101 | Changed by a plain comment after this spec is merged | Close and re-issue; merge then fix | Three lines change; the verify report and branch stay. |
| Q7 What Render follows | A fixed branch `deploy`, fast-forwarded by the script | Script changes the branch with the Render API; owner changes it by hand | Render follows one branch; no secret and no manual step. Git cannot hold both `release` and `release/…`, so the name is `deploy`. |
| Q8 Sprint name | `sprint-N`, counted up by the script | Date; a name typed each time | Matches "one per sprint" and needs no input. |

## Design

Nothing visible to users changes in the pages; no design card.

## Open questions
