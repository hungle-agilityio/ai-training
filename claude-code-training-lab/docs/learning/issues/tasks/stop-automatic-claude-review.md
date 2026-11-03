# [TASK] Stop the automatic Claude review; keep @claude on request

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-11-03
- **Type:** Task
- **Labels:** `task`, `tooling`, `github_actions`, `agent:manual`

## Summary

Claude reviews every pull request on GitHub each time a commit is pushed. Each run uses the owner's Claude plan, and on one pull request three runs in a row each found new small points, so the reviews did not settle by themselves. The owner wants a review only when they ask for one, by writing `@claude` in a comment. Nothing visible to users changes.

## Scope

- **Included:** remove the automatic review on GitHub; keep the answer to a comment that mentions `@claude`; write down the removal, its reason and its date in the project's list of removed things.
- **Not included:** line-by-line comments when `@claude` is asked for a review (the answer stays one comment); changing the automatic checks (lint, types, tests); removing the Claude GitHub App or its secret.

## Done when

- [ ] When a pull request into `main` is opened or a commit is pushed to it, no Claude review must start.
- [ ] When someone writes `@claude review this pull request` on a pull request, Claude must answer with one review comment.
- [ ] When the project's list of removed things is read, it must show the automatic review, the date 2026-11-03 and the reason.
- [ ] When the automatic checks run on a pull request, they must still run as before.

## Steps to check the result

1. Merge this pull request.
2. Open any new pull request into `main`, or push a commit to an open one.
3. Look at the checks of that pull request.
4. Write `@claude review this pull request` as a comment on it.

## Expected result

The checks show only the automatic checks, no Claude review. A few minutes after the comment, Claude answers with one review comment.

## Environment

GitHub (`hungle-agilityio/ai-training`)

## Attachments

None.
