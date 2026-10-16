# Lesson 2: Your First Conversation with Claude

- **Course:** Claude 101 (lesson 2 of 13)
- **Source:** https://academy.claude.com/courses/claude-101/your-first-conversation-with-claude
- **Date:** 2026-10-12
- **Status:** Done

All exercises use the ReviewRadar project (see the root `README.md`).

## Exercises

### Ex 1: Weak vs strong prompt

**Initial prompt:**
```
Help me design the review model.
```
**Link:** https://claude.ai/share/22784be9-5363-41f9-a6c7-8c06a447cd9e

**Improved prompt:**
```
I'm building ReviewRadar, a Django app that collects customer reviews for multi-branch businesses. I follow clean architecture: models hold data only, logic lives in the service layer (reviews/services.py).

Design the Django models for the reviews app: which entities I need (business, branch, review, sentiment, reply draft), their fields, and relationships.

Rules: use type hints. Show a table of entities and fields first, then the model code. Mention 2 design trade-offs. Keep code under 80 lines. Do not edit any files yet, just propose.
```
**Link:** https://claude.ai/share/22784be9-5363-41f9-a6c7-8c06a447cd9e


### Ex 2: Iterate

**Initial prompt:**
```
Draft a reply to this 2-star review of our Downtown branch: "Waited 50 minutes past my appointment time and nobody apologized." Keep it professional.
```
**Link:** https://claude.ai/share/2c0fb727-c80e-4293-bbdf-5b0a5f7de34c

**Improved prompt** (refine step by step in the same chat):
```
Shorten it to 3 sentences.
```
```
Make the tone friendlier and less corporate.
```
```
Go back to the original draft and add: offer a free follow-up visit and mention the branch manager by role. Then compare it with the version after the previous step.
```
**Link:** https://claude.ai/share/2c0fb727-c80e-4293-bbdf-5b0a5f7de34c


## Key takeaways

- Prompt = **stage** (role, goal, background) + **task** (specific action) + **rules** (style, format, examples, limits).
- Write naturally and concisely, like talking to a coworker. Context matters more than clever wording.
- Uploaded files (PDF, DOCX, CSV, TXT, PNG, JPEG) are a shortcut to context. Claude reads charts and images too.
- Sonnet is the default; Opus is for complex multi-step work. **Changing model starts a new chat.**
- Extended thinking helps complex analysis but adds latency. Leave it off for simple tasks.
- Iterate: follow-up questions, specific feedback, or redirect / new chat. Pencil icon edits and resends a message.
- Memory saves context automatically; "Instructions for Claude" is what you write yourself.
