# Intent: notify-fix

## Problem

The owner got no phone message from the loop from 2026-11-02 to 2026-11-04. Three things went wrong at once: the tmux loop had died (probably a restart of the Mac mini) and nothing started it again or said so; the main checkout was left on a feature branch, which the tick reported only once; and the ntfy app on the phone was not subscribed to the loop's topic. When messages do arrive, all sixteen kinds ring the same, so a "started #149" sounds as urgent as a failed build.

## Goal

The owner hears the phone only when the loop needs them or something broke, sees the other messages silently in the ntfy app, learns when the loop starts again after a restart, and is reminded until a wrong checkout branch is fixed.

## Users

The owner (`hungle-agilityio`), on the phone with the ntfy app; the loop on the Mac mini.

## Out of scope

- Slack (stays optional as today, not set up) and any new channel or account (email, healthchecks.io).
- A warning when the Mac mini is off or the loop dies without a restart (no outside watcher).
- Restarting the loop by itself while the machine runs (it would undo a deliberate "dừng loop").
- New message kinds other than "loop started"; changing the texts of today's messages.
- Messages from the Project threads (they already notify in the Claude app).
