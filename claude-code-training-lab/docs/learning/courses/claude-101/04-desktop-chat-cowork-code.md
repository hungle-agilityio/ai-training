# Lesson 4: How You'll Work with Claude on Your Desktop

- **Course:** Claude 101 (lesson 4 of 13, ~10 min)
- **Source:** https://academy.claude.com/courses/claude-101/claude-desktop-app-chat-cowork-code
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic.

## Exercises

### Ex 1: Pick the right shape of work

**Where:** Claude.ai (Chat)

Expected answers (check yourself after running both prompts):

| # | Task | Expected |
|---|------|----------|
| 1 | Ask what a drop in the Airport branch rating means, from a dashboard screenshot | Chat |
| 2 | Brainstorm categories for review topics (waiting time, price, staff...) | Chat |
| 3 | Turn 50 exported review files into one monthly summary memo saved in a folder | Cowork |
| 4 | Every Monday, gather last week's reviews and prepare a briefing | Cowork (scheduled) |
| 5 | Implement the Review model, service and tests in the Django repo | Claude Code |
| 6 | Debug a failing pytest in the repo | Claude Code |

**Initial prompt:**
```
Which Claude tool should I use for these tasks? 1) Understand a dashboard screenshot. 2) Brainstorm review topic categories. 3) Summarize 50 review files into a memo. 4) Weekly review briefing. 5) Implement Django models and tests. 6) Debug a failing pytest.
```
**Link:** https://claude.ai/share/ed221ab3-1da3-4396-88a2-c7aebba3273f

**Improved prompt** (new chat):
```
Claude desktop has three ways of working: Chat (turn-by-turn exchange), Cowork (hand off a whole multi-step task, may be scheduled, outputs saved as files), and Claude Code (work directly in a codebase). For each task below, pick one and give a one-line reason based on the shape of the work.

1) Understand what a drop in the Airport branch rating means, from a dashboard screenshot.
2) Brainstorm review topic categories.
3) Summarize 50 exported review files into one monthly memo saved in a folder.
4) Every Monday, gather last week's reviews and prepare a briefing.
5) Implement the Review model, service and tests in a Django repo.
6) Debug a failing pytest in the repo.

Output: a table with columns # | Tool | Reason.
```
**Link:** https://claude.ai/share/d71423a5-9b06-4d59-8313-9a983d361279


### Ex 2: Build in a codebase (Claude Code)

**Where:** Claude desktop, Code tab, Local, folder `claude-code-training-lab`

Run both in a fresh session. Do not commit. After the first prompt, revert any change with `git checkout reviews/models.py`.

**Initial prompt** (permission mode: Manually approve):
```
Create the Review model in reviews/models.py.
```

**Improved prompt** (permission mode: Plan):
```
Propose a plan for the Review model in reviews/models.py: fields, relations to Branch, and where sentiment is stored. Follow the project rules in CLAUDE.md and the root README.md. Do not change any files yet.
```

## Key takeaways

- Three shapes of work, not three tools to memorize:
  - **Chat:** turn-by-turn. The answer shapes your next question.
  - **Cowork:** hand off a whole task (multi-step, saved files, cross-tool, scheduled). Review the plan and output.
  - **Claude Code:** work directly in a codebase (read, write, test, run commands, git).
- Notice the kind of work first; the right tab follows.
- For a hand-off, describe the **outcome**, not the first question you would ask.
- Claude Code: **Local** (a folder on your machine) or **Cloud** (a GitHub repo, keeps running when the app closes).
- Claude Code permission modes: **Manually approve** (every change), **Accept edits** (edits applied automatically), **Plan** (plan first, then changes).
- Stay in control: review plans, watch progress, require approval for consequential actions.
