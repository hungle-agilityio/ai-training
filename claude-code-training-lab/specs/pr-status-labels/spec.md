# Spec: pr-status-labels

## Summary

The `work-queue` loop gives each of its open pull requests exactly one status label and changes it as the pull request moves. Nothing in the app changes; the labels show on GitHub only.

| Label | Meaning |
|---|---|
| `pr:ready-for-review` | CI is green and the verify report passed; waiting for the owner |
| `pr:changes-requested` | the owner sent `/redo` and the loop is working on it |
| `pr:blocked` | the loop cannot go on without the owner; the reason is a comment on the pull request |
| `pr:ci-failed` | CI is still red after the loop tried to fix it twice |

## Acceptance criteria

- **AC1. Labels exist.** Before it sets a label, the loop creates any missing `pr:*` label with `gh label create` (colors: ready `0E8A16`, changes-requested `FBCA04`, blocked `B60205`, ci-failed `D93F0B`), each with a one-line description from the table above.
- **AC2. Exactly one.** Setting a status label removes the other three in the same `gh pr edit <n> --add-label ... --remove-label ...` call. After any loop run, no open pull request of the loop has two `pr:*` labels.
- **AC3. After opening.** After it opens a pull request (`work-queue` step 8), the loop waits for CI in the same run with `gh pr checks <n> --watch`, at most 15 minutes. Green: `pr:ready-for-review`. Red: AC4. Still running after 15 minutes: no label yet; the next run checks again (AC7).
- **AC4. Red CI.** The loop reads the failing check, fixes it on the same branch (tests and gates as in any build), pushes, and waits for CI again (AC3). It does this at most twice per round of work; a round starts when the pull request is opened and at each counted `/redo`. Each attempt is a comment on the pull request with the marker, "CI fix attempt 1 of 2" or "2 of 2", and what failed. Still red after the second attempt: `pr:ci-failed`, and a comment with the marker naming the failing check and what was tried.
- **AC5. Redo.** When the loop counts a `/redo` (`work-queue` section 1), it sets `pr:changes-requested` before it starts. After it pushes the redo commits, it waits for CI as in AC3 and AC4, which ends in `pr:ready-for-review` or `pr:ci-failed`.
- **AC6. Blocked.** The loop sets `pr:blocked` and comments the reason (with the marker) when it cannot go on without the owner: a merge conflict with `main`, a hook that blocks a command the redo needs, or a `/redo` it cannot act on without changing the requirement. A blocked pull request is not retried on later runs until a new `/redo` from the owner, which sets `pr:changes-requested` again (AC5).
- **AC7. Every run.** In section 1, for each open pull request of the loop that has no status label (a pull request opened before this change, or one whose CI was still running), the loop reads `gh pr checks <n>` and sets the label by AC3 and AC4. A pull request labelled `pr:ready-for-review` whose CI is now red is handled as in AC4.
- **AC8. Merged or closed.** When a pull request of the loop is merged or closed, the loop removes any `pr:*` label from it (and, as today, `agent:review` from the issue).
- **AC9. Permission.** `.claude/settings.json` allows `Bash(gh pr edit:*)`, so the loop never stops on a prompt when it changes a label. Nothing else in the allow, ask or deny lists changes.
- **AC10. Status.** The Status step in `.claude/project-instructions.md` reports, for each issue, its `agent:*` label, the pull request, the pull request's `pr:*` label and the report link.
- **AC11. Recorded.** A decision record (ADR-013) states the four labels, the "exactly one" rule, the two CI fix attempts, and that the ADR-012 phase 2 scripts must keep these rules. `knowledge/decisions/README.md` lists it.

## Edge cases

- Empty: no open pull request of the loop, nothing to label.
- Large data: up to 5 open pull requests (the current cap); each run checks each one once.
- Permissions: only the loop sets `pr:*` labels. If the owner changes one by hand, the loop's next action on that pull request sets the label again by these rules.
- CI not configured for a branch, or `gh pr checks` reports no checks: treat as still running (AC3), never as green.
- The loop's labels and comments use the owner's login (the loop's token); the marker `<!-- work-queue -->` stays on every comment.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. When to set `pr:ready-for-review` | Wait for CI in the same run, at most 15 minutes | Check at the next run (up to 30 minutes without a label); set it at once and correct later | The label is set early and never says something false |
| Q2. Red CI | The loop tries to fix it twice, then `pr:ci-failed` | `pr:ci-failed` at once and the owner sends `/redo` | The owner approved this behaviour in the proposal |
| Q3. Issue labels `agent:*` | Keep them; `pr:*` goes on the pull request only | Drop `agent:review` | Smaller change; Status and the ADR-012 plan read `agent:*` |
| Q4. Permission to change labels | Allow `Bash(gh pr edit:*)` | Allow it and limit it in the hook to `pr:*` labels | Simpler; the loop already opens pull requests, editing one adds little risk |
| Q5. Merged or closed pull requests | Remove the `pr:*` label | Leave it | No stale status on finished pull requests |

## Design

Nothing visible to users of the app; the labels show on GitHub only.

## Open questions
