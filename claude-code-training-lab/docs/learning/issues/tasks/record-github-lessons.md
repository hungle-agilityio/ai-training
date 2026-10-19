# [TASK] write down what we learned from connecting the assistant to GitHub

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-10-19
- **Type:** Task
- **Labels:** `task`, `tooling`

## Summary

Write down, in the project's shared notes, the problems met while connecting the AI assistant to GitHub and publishing the epics, so that nobody has to find them again. The notes are read by the assistant before it plans and reviews. The work touches the project's notes and its list of decisions. Nothing visible to users of the ReviewRadar app changes.

Four problems are recorded. First, a GitHub access key that cannot see the repository gives a misleading "not found" answer. Second, the GitHub connection is missing when the assistant is opened in the wrong folder. Third, attaching one issue to another needs a number that is not the issue number. Fourth, an issue whose boxes are all ticked cannot pass the publishing check. One decision is recorded too: why the project's settings live in the lab folder and the assistant is opened there.

## Scope

- **Included:** four entries in the list of known problems, each with what is seen, the cause and the fix; one decision record; a line for it in the list of decisions.
- **Not included:** any rule about the business; the details of the work done in the other issues; changing how the project is organised.

## Done when

Each item must be something a person can check without technical help.
- [ ] The list of known problems has four new entries, each with what is seen, the cause and the fix.
- [ ] A new decision record explains why the settings live in the lab folder and where the assistant must be opened.
- [ ] The list of decisions shows the new record.
- [ ] No entry repeats a decision or a problem that is already written down.

## Steps to check the result

1. Open the list of known problems in the project's notes and find the four new entries at the end.
2. For each one, check that it says what is seen, why it happens and what to do.
3. Open the list of decisions and find the new record; open it and check that it gives the reason and the consequence.

## Expected result

A person who meets one of the four problems finds its entry and knows what to do without asking. The decision record answers why the settings are not at the top of the repository.

## Environment

dev

## Attachments

Nothing attached.
