# Lesson 12: Other Ways to Work with Claude

- **Course:** Claude 101 (lesson 12 of 13, ~15 min)
- **Source:** https://academy.claude.com/courses/claude-101/other-ways-to-work-with-claude
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic.

## Exercises

### Ex 1: Pick the right Claude tool

**Where:** Claude.ai (regular chat)

Expected answers (check yourself):

| # | Task | Expected |
|---|------|----------|
| 1 | Summarize a long Slack thread about a bug and hand it to a developer | Claude Tag |
| 2 | Fix lint errors and write release notes in the repo | Claude Code |
| 3 | Prototype the branch score dashboard UI from a sketch | Claude Design |
| 4 | Update assumptions in a pricing spreadsheet without breaking formulas | Claude for Excel |
| 5 | Fill the same web form 20 times | Claude in Chrome |
| 6 | Turn an outline into a first-draft deck in the team template | Claude for PowerPoint |

**Initial prompt:**
```
Which Claude tool should I use for these tasks? 1) Summarize a Slack thread about a bug. 2) Fix lint errors and write release notes. 3) Prototype a dashboard UI from a sketch. 4) Update assumptions in a pricing spreadsheet. 5) Fill a web form 20 times. 6) Turn an outline into a deck in our template.
```
**Link:**

**Improved prompt** (new chat):
```
Claude runs in several tools: Claude Code (agentic coding in terminal, IDE or browser), Claude Tag (Claude inside Slack), Claude Design (interactive UI prototypes as editable artifacts), Claude for Microsoft 365 (sidebars in Excel, PowerPoint, Word, Outlook), Claude in Chrome (browser sidebar that can take actions), and Claude.ai (general tasks). For each task, pick one tool and give a one-line reason.

1) Summarize a long Slack thread about a bug and hand it to a developer.
2) Fix lint errors and write release notes in a repo.
3) Prototype a branch score dashboard UI from a sketch.
4) Update assumptions in a pricing spreadsheet without breaking formulas.
5) Fill the same web form 20 times.
6) Turn an outline into a first-draft deck in the team template.

Output: a table with columns # | Tool | Reason.
```
**Link:**

### Ex 2: Explore a codebase with Claude Code

**Where:** Claude Code (terminal or desktop, folder `claude-code-training-lab`). Read-only: no files should change.

**Initial prompt:**
```
Tell me about this repo.
```

**Improved prompt:**
```
Explore this repo without changing any files. Explain: (1) the project structure in 8 lines, (2) which files are still empty skeletons, (3) where a Review model, its repository, and a sentiment service should go according to the structure, (4) what would need to change to add a new Django app. Quote file paths. If something is unclear, say so instead of guessing.
```

After running, run `git status` and confirm nothing changed.

### Ex 3: Prototype with Claude Design

**Where:** Claude.ai (paid plans; Claude Design is in beta, skip if you do not see it)

**Initial prompt:**
```
Design a dashboard.
```
**Link:**

**Improved prompt** (new chat):
```
Using Claude Design, create an interactive prototype of the ReviewRadar dashboard for a clinic owner who is not technical. One screen. Show: average rating per branch (Airport 2.0, Downtown 4.0, Riverside 3.7) as cards, red highlight for any branch under 3.5, a list of the top 3 complaint themes (waiting time, parking, phone line) with counts, and a button "Draft replies". Clean, calm, mobile friendly. Make it an artifact I can edit.
```
**Link:**

## Key takeaways

- Claude.ai is one way to work with Claude; specialized tools fit specific workflows.
- **Claude Code:** agentic coding in terminal, IDE, browser or Slack. Understands the codebase, runs commands, writes code and tests, makes commits. For developers.
- **Claude Tag:** Claude in Slack. Tag it to summarize threads, prepare for meetings, or hand a bug report to Claude Code.
- **Claude Design:** idea, sketch, or screenshot to an interactive prototype as an editable artifact. Beta, paid plans. Can be handed to Claude Code to build.
- **Claude for Microsoft 365:** sidebars in Excel (formulas, errors, pivots), PowerPoint (decks in your template), Word (drafts, tracked changes), Outlook (triage, replies; beta, installed separately).
- **Claude in Chrome:** browser sidebar that can observe and act (summarize, fill forms, navigate). Paid plans only. Use for low-risk tasks on trusted sites; it asks permission before high-risk actions.
- **Claude Cowork:** multi-step tasks and file work on desktop.
- Choose by workflow: where the work happens decides the tool.
