# Lesson 5: Introduction to Projects

- **Course:** Claude 101 (lesson 5 of 13, ~15 min)
- **Source:** https://academy.claude.com/courses/claude-101/introduction-to-projects
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic and are done on Claude.ai.

## Setup (do once)

Claude.ai > Projects > + New Project.

- **Name:** `ReviewRadar Learning Lab`
- **Description:** `Learning Claude by building ReviewRadar, a Django app for multi-branch review management.`
- **Visibility:** private
- **Instructions** (paste into Instructions, then Save instructions):
  ```
  Context: I'm learning Claude by building ReviewRadar, a Django app that collects customer reviews for multi-branch businesses, classifies sentiment with the Claude API, and suggests replies.
  Process: for design questions, list assumptions first, then give the answer.
  Tone: concise, plain language, no filler. Reply in Vietnamese, keep technical terms and code in English.
  Requirements: Python code must have type hints. Logic goes in a service layer, not in views. End every design answer with one trade-off.
  ```
- **Knowledge:** upload `README.md` and `docs/courses/claude-101/02-first-conversation.md`, `03-getting-better-results.md`, `04-desktop-chat-cowork-code.md` (descriptive file names help Claude find the right file).

## Exercises

### Ex 1: Instructions make the difference

**Where:** Claude.ai (outside, then inside the Project)

**Initial prompt** (new chat outside the Project):
```
How should I structure the code that classifies a review's sentiment?
```
**Link:**

**Improved prompt** (same question, new chat inside the Project):
```
How should I structure the code that classifies a review's sentiment?
```
**Link:**

### Ex 2: Knowledge base and file names

**Where:** Claude.ai (inside the Project)

**Initial prompt** (does not name a file):
```
What are the ways to fix a response that is too generic?
```
**Link:**

**Improved prompt** (names the file):
```
According to 03-getting-better-results.md, what are the ways to fix a response that is too generic? Quote the exact line from the file.
```
**Link:**

### Ex 3: Vague vs specific instructions

**Where:** Claude.ai (inside the Project)

Replace the Project instructions with the vague version, run the prompt in a new chat, then restore the specific instructions from Setup and run it again in a new chat.

**Initial prompt** (Project instructions set to `Help me with my Django project.`):
```
Design the Branch and Review models.
```
**Link:**

**Improved prompt** (specific instructions restored):
```
Design the Branch and Review models.
```
**Link:**

## Key takeaways

- A project is a workspace for **ongoing work**: its own chats, knowledge base, and instructions.
- **Instructions** apply to every chat in the project. Write them with four parts: context, process, tone and style, specific requirements. Vague instructions give inconsistent results.
- **Knowledge** is reused in every chat, so you do not re-upload files. Supported types: PDF, DOCX, CSV, TXT, HTML, plus Google Drive.
- Use **descriptive file names** and **reference files by name** in questions.
- Large knowledge bases switch to retrieval (RAG) near the context limit, so Claude pulls only the relevant parts.
- Context does **not** carry across chats unless it is in the project knowledge.
- Keep knowledge current: outdated files give outdated answers. Start with one focused use case.
- Sharing and permission levels (view, edit, owner) are for Team and Enterprise plans.
