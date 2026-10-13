# Lesson 9: Enterprise Search

- **Course:** Claude 101 (lesson 9 of 13, ~15 min)
- **Source:** https://academy.claude.com/courses/claude-101/enterprise-search
- **Date:** 2026-10-13
- **Status:** In progress

Enterprise Search is available on Team and Enterprise plans only and must be enabled by a workspace admin. Free, Pro and Max users can skip the hands-on part. The exercises below simulate it with a regular chat and a connector.

## Setup (do once)

Create a Notion page named `ReviewRadar Spec` and paste in `docs/reviewradar-project-context-2026-10.md` (nothing sensitive). Confirm the Notion connector is on in Claude.ai (Customize > Connectors).

## Exercises

### Ex 1: Ask across a connected source

**Where:** Claude.ai (regular chat, Notion connector on)

**Initial prompt:**
```
What are our testing rules?
```
**Link:**

**Improved prompt** (new chat):
```
Search my Notion for the page "ReviewRadar Spec". Answer: what are the testing rules, and which section defines them? Cite the page and the section for each rule. If you cannot find the page or the rule, say so instead of guessing.
```
**Link:**

### Ex 2: Design the admin setup for a fictional org

**Where:** thinking exercise, no chat needed

Pretend you are the Owner of "ReviewRadar Co" (Team plan) and fill in the setup. Check yourself against the lesson.

| Setup field | Your answer |
|-------------|-------------|
| Documents connector (required) | |
| Chat connector (required) | |
| Email connector (recommended) | |
| Project name (shown as "Ask [Name]") | |
| Description | |
| Two example questions a new engineer would ask | |

Self-check: you must have one Documents and one Chat connector; the name shows as "Ask [Name]" in everyone's sidebar; each user still authenticates with their own accounts.

## Key takeaways

- Enterprise Search adds an **"Ask {Org Name}"** project to the sidebar: a pre-built, organization-wide project with the company knowledge base loaded.
- It is built for information gathering with custom instructions from Anthropic, unlike a regular chat with connectors.
- It searches connected tools (e.g. Drive, SharePoint, Slack, Gmail), **synthesizes one answer and cites sources**.
- Question types: catch up on what you missed, policy and process, research and analysis, onboarding, project tracking.
- Setup: an **admin** connects a Documents connector and a Chat connector (email recommended), names the project, and finishes; then each **user** authenticates with their own accounts.
- Available on **Team and Enterprise** only; an admin must complete setup before members can use it.
- **Security:** you only see what you can already access in the original tool; conversations stay private; connected data is not indexed or stored separately.
- More connectors give more complete answers.
