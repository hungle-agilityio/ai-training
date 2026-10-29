# Intent: loop-ux

## Problem

The owner runs the loop from the phone, and three things take more effort than they should:

- **Notifications.** ntfy says when a build fails, when the plan limit pauses the loop and when the queue is empty. It says nothing when a build starts, when a pull request needs the owner (`pr:blocked`, `pr:ci-failed`), when a pull request is merged, or when the loop stops taking issues because too many pull requests are waiting. In that last case it even says "queue empty" while ready issues are waiting.
- **Merging.** The only way today is to ask a thread, which runs `gh pr merge` through Remote Control on the Mac mini, where auto mode sometimes refuses it. The owner wants to write "lgtm" on the pull request, or ask in the project chat, or press Merge on GitHub, and have the rest happen: the merge, then the new `main` in the Mac mini checkout.
- **Change requests.** Only a comment starting with `/redo` counts, and only when it is newer than the last commit. A CI-fix commit makes an unfinished request look done, a second request hides the first, and comments on lines of code are not read. Nobody can see which request was done.

## Goal

The owner writes on the pull request the way people normally review: a plain comment or a comment on a line asks for a change, a short "lgtm" merges. Each request shows on GitHub whether the loop took it (👀), did it (🚀) or could not (😕), and the next round only does what is still open. The phone gets one message for each step that matters.

## Users

The owner (`hungle-agilityio`), on the phone (ntfy, GitHub) and in the project chat; the tick and the loop builds on the Mac mini.

## Out of scope

- Any change to the app (`reviewradar/`, `reviews/`).
- Anyone but the owner approving, merging or asking for changes: the repository is public, and other logins are ignored.
- GitHub's Approve and Request changes buttons: GitHub does not offer them to the author of a pull request, and the owner is the author of every loop pull request.
- Pulling `main` on any computer other than the Mac mini.
- Spec pull requests: they keep today's route ("Merge PR spec").
