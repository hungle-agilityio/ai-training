# [TASK] protect the repository

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-10-19
- **Type:** Task
- **Labels:** `task`, `hosting`, `needs-info`

## Summary

Make sure nobody can change the main version of the project by accident: a change must go through a pull request with passing checks, and secrets must be caught before they leave the owner's computer. The work touches the settings of the repository on GitHub. Nothing visible to users of the ReviewRadar app changes.

Part of it is done: the file that names the reviewers, the weekly update of dependency versions, and the automatic checks on every pull request are in place. The rest cannot be switched on today. GitHub does not enforce the rules for the main version, nor the scanning for secrets, on a private repository without a paid team plan. A direct change to the main version was accepted in a test on 2026-10-19.

The owner decided to keep the repository private on the current plan and rely on discipline for now: the assistant is stopped from committing to the main version, and a person reviews and merges every pull request. This issue stays open until the repository becomes public or moves to a team plan.

## Scope

- **Included:** the rules on the main version (a pull request and passing checks are required, no forced changes, no deletion); only squash merges, and branches deleted after merge; secret scanning and push protection; a new test that a direct change to the main version is refused.
- **Not included:** paying for a plan or making the repository public (the owner decides that); the automatic checks and the dependency updates (already done).

## Done when

Each item must be something a person can check without technical help.
- [x] The reviewer file and the weekly dependency updates exist in the repository.
- [x] The automatic checks run on every pull request.
- [ ] When someone tries to change the main version directly, GitHub refuses it.
- [ ] Merging a pull request is only possible when the checks have passed.
- [ ] Only squash merges are offered, and branches are deleted after merge.
- [ ] A fake secret added in a test branch is stopped before it reaches GitHub.

## Steps to check the result

1. Try to send a small change directly to the main version. GitHub must refuse it.
2. Open a pull request whose checks fail. The merge button must be blocked.
3. Open a pull request whose checks pass. Only the squash merge option appears, and the branch is deleted after merging.
4. In a test branch, add a fake secret and try to send it. GitHub must stop it.

## Expected result

A direct change to the main version is refused, a merge needs passing checks, and a fake secret is stopped.

## Environment

dev

## Attachments

Nothing attached yet. To add: the refusal message from step 1 and the result of the secret test, once the plan allows it.
