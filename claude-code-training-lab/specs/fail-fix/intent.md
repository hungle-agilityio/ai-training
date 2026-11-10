# Intent: fail-fix

## Problem

A loop build that meets an existing test the issue does not let it change stops with `needs-decision`, and the tick never restarts that kind of stop, so the task and every task after it in the epic wait for the owner. It happened twice in two epics (#375 on 2026-11-09, #397 on 2026-11-10), both times a test capping a page's query count. The planning check `ops/pinned_tests.py` exists but sees only two of the four ways our tests cap queries (it missed 84 tests, among them the five that #397 and #399 would have broken), prints dozens of unrelated lines, and nothing makes anyone run it.

## Goal

1. Problems of this kind are caught before a build starts: when the Project thread writes the issue, and again by the tick before each build.
2. When a build still stops for a technical reason, the loop decides the fix itself, records it, and builds again at once, ahead of new work. The owner is asked only when the fix would change what users see, a business rule, security or data.

## Users

The owner, who reviews one epic pull request and no longer has to unblock tasks by hand; the Project thread that writes the issues; the loop.

## Out of scope

- Self-fixing anything that changes the requirement: a page, a text users read, a business rule, permissions, secrets, migrations or data.
- A limit that grows with the data (an N+1) is never accepted as a fix.
- Retries for other failure kinds (`transient`, `stopped`): they keep today's rules (ADR-018).
- Measuring a page's real query count before a build (needs a database run); the epic's query budget is written by the Project thread.
