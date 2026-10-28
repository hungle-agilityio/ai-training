# Spec: report-artifact-link

## Summary

The loop publishes the verify report as a private artifact before it opens the pull request, and a hook refuses a loop pull request whose body has no artifact link. Nothing visible to users of ReviewRadar; the change is in `.claude/` (settings, one hook and its tests, two skills), so the issue is `agent:manual`.

## Acceptance criteria

- **AC1.** `.claude/settings.json` `permissions.allow` contains `Artifact`. The hook `before-artifact-publish` is unchanged and still refuses a report under `out/verify/` whose masking check is not `clean` (its existing tests pass).
- **AC2.** In loop mode (`REVIEWRADAR_LOOP=1`), `before-github-command-check` denies `gh pr create` when the body has no `https://claude.ai/artifact/` link, with the reason "a loop pull request needs the verify report link (share-report)". With the link, `gh pr create` is allowed as today.
- **AC3.** The hook reads the body from `--body` / `-b` and from `--body-file` / `-F` (a path relative to the command's folder). In loop mode a `gh pr create` with no body (for example `--fill`) or with a body file it cannot read is denied.
- **AC4.** Outside loop mode, `gh pr create` behaves as today (asks for approval), with or without the link.
- **AC5.** `work-queue` step 8 runs in this order: `build-verify-report`, `share-report` (publish, link written to `report.json` under `share.url`), commit, push, pull request whose body has the link on the "Verify report" line.
- **AC6.** When `share-report` gives no link in loop mode (gate `BLOCKED`, or the publish fails or is refused), the loop opens no pull request: it labels the issue `agent:failed` and comments the reason with the `<!-- work-queue -->` marker, and the branch stays local, as for a review that stays open after round two.
- **AC7.** In a `/redo` round the loop republishes to the same URL (`share.url` in `report.json`), so the pull request link stays valid.
- **AC8.** `draft-pull-request` says that in loop mode the report line must be the artifact link; "not shared" with the local path stays allowed only in an interactive session.
- **AC9.** New tests in `.claude/hooks/tests/` cover AC2, AC3 and AC4 (loop without link denied, loop with link in `--body` allowed, loop with link in `--body-file` allowed, loop with `--fill` denied, interactive unchanged). Existing tests are unchanged and `uv run pytest -q` passes.
- **AC10.** `.claude/knowledge/KNOWN_PITFALLS.md` has one entry: an unattended session can only use a tool that is in the allow list; a tool that needs a prompt is skipped (seen on PR #41).
- **AC11.** After the merge, the next loop pull request has a `https://claude.ai/artifact/` link in its body, and `out/artifact-publish.log` on the Mac mini has an `allowed` line for that run. The owner checks this on the first loop run.

## Edge cases

- Empty: no report folder, or `report.json` without `share.url` after `share-report`: no pull request (AC6).
- Large data: a report page over the size limit is `BLOCKED` by the gate: no pull request (AC6).
- Permissions: the hook still gates every Artifact call on a file under `out/verify/`; allowing the tool does not let an unmasked report out.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. How does the loop get to publish? | Add `Artifact` to the allow list in `.claude/settings.json` | Allow it only in the loop start command; keep a Project thread publishing by hand | Simplest; the hook still gates reports; works the same for `claude -p` later |
| Q2. No link possible? | No pull request, `agent:failed`, comment the reason | Open the pull request with "not shared: reason" | Only this makes "every pull request has the link" true |
| Q3. How is it enforced? | `before-github-command-check` checks the `gh pr create` body in loop mode | Skill text only | Skill text alone already failed on PR #41 |
| Q4. Probe before the build? | Yes, one short run on the Mac mini confirms the cause | Skip | The loop transcript could not be read from the Project |

## Design

Nothing visible to users.

## Open questions
