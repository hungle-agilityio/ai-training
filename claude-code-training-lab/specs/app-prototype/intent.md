# Intent: app-prototype

## Problem

The owner reads a static design card (four pictures of one feature) before the spec is fixed, and cannot click through the flow. Each feature has its own card, so nothing shows the whole app in one place. After the build, nothing puts the built screen next to the design: `design/README.md` says `capture-before-after` compares them, but that program compares `main` with the branch and never opens the design. A layout bug can reach the owner unnoticed: at phone width the dashboard's "Location scores" table makes the whole page 700 px wide.

## Goal

One clickable prototype of the whole app (`design/app/prototype.html`, published as a private Artifact) is the source of truth for every screen. A request that changes what users see updates the prototype first; the owner tries it and approves it ("Prototype ổn") before epics and tasks are split. The verify report of a build shows each designed state next to the built screen, so the owner sees any difference at a glance.

## Users

- The owner: tries every screen and state before the work is split, and compares design with build in the verify report.
- The Project threads: update the prototype at the new Prototype step and name its states in the issues.
- The loop: captures the prototype states next to the built screens.
- Clients: can be shown the prototype by the owner (sharing stays the owner's choice).

## Out of scope

- A new-project kickoff with the prototype step (the `agent-flow-starter` template): a follow-up.
- A pixel diff or any automatic failure on a difference between design and build (Q5).
- Changing the app's look; the prototype matches `main` 5213e39, except the phone-width fix of T4.
- Removing the old `design/<feature>/` folders: they stay as history.
