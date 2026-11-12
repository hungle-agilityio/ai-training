# Intent: settings-paste-reminder

## Problem

After every flow change the owner pastes `.claude/project-instructions.md` into the Project settings by hand (Day 12 #466, Day 13 #482, member assignment #484). Nothing tells the owner when the two drift apart, so threads can follow rules that are no longer on `main` (retro issue #485).

## Goal

At each release, the release plan says when `.claude/project-instructions.md` changed since the last release, and the release thread then gives the owner the whole file to paste once.

## Users

The owner.

## Out of scope

- A checksum line in the Project settings that threads compare (owner chose the release reminder, 2026-11-12).
- Writing the Project settings automatically (no API for it).
- Changes to the file between releases: they are pasted at the next release, not after each merge.
