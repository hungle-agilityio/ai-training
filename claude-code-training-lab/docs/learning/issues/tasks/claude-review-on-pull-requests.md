# [TASK] Let Claude review each pull request on GitHub and answer @claude

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-11-03
- **Type:** Task
- **Labels:** `task`, `tooling`, `github_actions`, `agent:manual`

## Summary

Today a pull request gets the automatic checks (lint, types, tests) and the owner's review. A second reviewer that reads every pull request on GitHub, and answers when someone writes `@claude` in a comment, gives the owner findings before they read the diff. It uses the Claude GitHub App and `anthropics/claude-code-action`. It touches only `.github/workflows/`; nothing visible to users.

## Scope

- **Included:** the Claude GitHub App installed on `hungle-agilityio/ai-training` and its secret, both by the owner with `/install-github-app`; a workflow that reviews a pull request when it is opened or updated; a workflow that answers a comment that mentions `@claude`; the review prompt points at the project rules (`claude-code-training-lab/.claude/rules/`) and asks for findings only, never an approval.
- **Not included:** letting the action push commits, merge, approve or label; changing `checks.yml`; reviewing the spec pull requests in a different way.

## Done when

- [ ] When a pull request is opened into `main`, a Claude review comment must appear on it within 10 minutes.
- [ ] When someone writes a comment with `@claude` on an issue or a pull request, Claude must answer in a comment.
- [ ] When the review runs, the pull request must not be approved, merged or changed by it.
- [ ] When the workflow file is read, no secret value must be written in it (only `${{ secrets.<name> }}`).

## Steps to check the result

1. Merge this pull request.
2. Open any new pull request into `main`.
3. Wait for the checks and look at the comments of the pull request.
4. Write a comment `@claude what does this change do?` on that pull request.

## Expected result

A review comment from Claude is on the pull request, and a second comment answers the question. The pull request is still open and not approved.

## Environment

GitHub (`hungle-agilityio/ai-training`)

## Attachments

Exercise: "GitHub Actions @claude on the training repo" and "@claude review fires on your next PR; evaluate its comments".
