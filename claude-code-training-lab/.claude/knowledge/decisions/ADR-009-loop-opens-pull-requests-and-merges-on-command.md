# ADR-009: The loop opens pull requests and merges the ones the user marks

- Status: Accepted
- Date: 2026-10-26

## Context

ADR-008 stopped the loop at a local commit and asked the user before every push. The user wants to review several pull requests at once, while the loop keeps working the rest of the queue, and wants Claude to merge what they approve. Until now `rules/git.md` and `rules/security.md` said Claude never merges and every push or pull request needs approval for that item.

## Decision

The user explicitly changed those rules for loop mode (2026-10-26):
- The loop pushes its own issue branch and opens the pull request with the verify report link; no preview.
- The user approves by commenting `/merge` on the pull request. Only the owner's comment counts. The loop then checks that the checks are green and the pull request is mergeable, and runs `gh pr merge --merge`, keeping the branch.
- `/redo <what>` sends a pull request back; the loop adds commits to the same branch.
- At most 5 pull requests wait at once; an issue with `Depends on #M` waits until #M is merged.
- One private "Review queue" artifact, updated in place, lists the waiting pull requests. A push notification says when the queue is empty.

Rejected:
- **GitHub "Approve" as the signal:** the pull request is opened with the user's own token, and GitHub does not let an author approve their own pull request; `gh pr review` is also denied.
- **Merge without a marker, or when checks pass:** no branch protection on the free plan, so the marker is the only human gate left.
- **Wait for approval before pushing:** it blocks the queue, which is what the loop is for.

## Consequences

- Interactive sessions keep the old rules: no merge, approval per push. Only loop mode, and only for its own branches, is exempt.
- Checks cannot be required by GitHub, so the loop verifies them itself before it merges.
- Two waiting pull requests can conflict; the later one is sent back as a redo.
- `.claude/settings.json` still denies `gh pr merge` and asks for `git push` and `gh pr create`; a person must change that file (allow those three for the loop) before the loop can do this.
