# Lesson 7: Working with Skills

- **Course:** Claude 101 (lesson 7 of 13, ~15 min)
- **Source:** https://academy.claude.com/courses/claude-101/working-with-skills
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic and are done on Claude.ai.

## Setup (do once)

- Settings (your name, lower-left) > Capabilities > turn on **Code execution and file creation**.
- Customize > Skills: confirm the built-in skills are listed.

## Exercises

### Ex 1: Project or Skill?

**Where:** Claude.ai (regular chat)

Expected answers (check yourself):

| # | Item | Expected |
|---|------|----------|
| 1 | Branch directory and escalation contacts | Project (knowledge) |
| 2 | Steps to write a reply to a negative review | Skill (process) |
| 3 | Past 6 months of exported reviews | Project (knowledge) |
| 4 | Weekly sentiment report with the same structure every time | Skill (process) |
| 5 | The clinic's brand voice guide | Project (knowledge) |
| 6 | Checklist for escalating a legal complaint | Skill (process) |

**Initial prompt:**
```
Should these be a Claude Project or a Claude Skill? 1) Branch directory. 2) Steps to reply to a negative review. 3) Past 6 months of reviews. 4) Weekly sentiment report. 5) Brand voice guide. 6) Legal complaint escalation checklist.
```
**Link:**

**Improved prompt** (new chat):
```
In Claude, Projects store knowledge (reference material Claude draws on in every chat) and Skills define process (the steps and method Claude follows each time a task comes up). For each item, answer Project or Skill with a one-line reason.

1) Branch directory and escalation contacts.
2) Steps to write a reply to a negative review.
3) Past 6 months of exported reviews.
4) Weekly sentiment report with the same structure every time.
5) The clinic's brand voice guide.
6) Checklist for escalating a legal complaint.

Output: a table with columns # | Project or Skill | Reason.
```
**Link:**

### Ex 2: Built-in skill (Excel file creation)

**Where:** Claude.ai (regular chat)

**Initial prompt:**
```
Make a spreadsheet of reviews.
```
**Link:**

**Improved prompt** (new chat):
```
Create an Excel spreadsheet to track customer reviews for a 3-branch clinic (Downtown, Riverside, Airport). Columns: Date, Branch, Rating (1-5), Review text, Sentiment, Replied (Yes/No). Add 10 sample rows. Add a second sheet with, per branch, the review count and average rating using formulas, and highlight branches with an average below 3.5. Give me a downloadable .xlsx file.
```
**Link:** https://claude.ai/share/2a9eada7-f29b-4902-87d6-f302b188b93f

Open the downloaded file and check that the formulas are real formulas, not pasted numbers.

### Ex 3: Create a custom skill

**Where:** Claude.ai (new chat; answer Claude's questions, then select Save skill)

**Initial prompt:**
```
Create a skill for replying to reviews.
```
**Link:**

**Improved prompt** (new chat):
```
Create a skill called "review-reply". Use it whenever I give you a customer review and ask for a reply.

Process: 1) classify the review as positive, negative, neutral or mixed; 2) pick the reply type; 3) draft the reply.
Rules: reply in the language of the review. Maximum 3 sentences. Never admit legal liability. Never promise refunds; offer a follow-up visit instead. For negative reviews, apologize once, name the specific problem, and give a next step. Sign as "The [Branch] Team".
Escalation: if the review mentions injury, legal action, or a named staff member, do not draft a reply. Output "ESCALATE" and a one-line reason.
Output format: first line "Sentiment: <label>", then the reply.

Ask me any questions you need, then save it.
```
**Link:**

### Ex 4: Test the skill (skill off vs on)

**Where:** Claude.ai (new chats; toggle in Customize > Skills > review-reply)

**Initial prompt** (skill turned off):
```
Reply to this review for our Airport branch: "Waited 50 minutes and nobody apologized."
```
**Link:**

**Improved prompt** (skill turned on, same text, new chat):
```
Reply to this review for our Airport branch: "Waited 50 minutes and nobody apologized."
```
**Link:**

Then try one escalation case in the same chat: `Reply to this review for our Downtown branch: "My mother fell in your waiting room and I'm talking to a lawyer."` The skill should answer ESCALATE.

## Key takeaways

- A **skill** is a bundle of instructions, scripts, and resources that Claude loads when a task calls for it. It makes a specialized task repeatable.
- **Projects store knowledge, skills perform tasks.** Project = reference material across chats. Skill = the steps and method followed each time.
- Two kinds: **Anthropic skills** (Excel, Word, PowerPoint, PDF creation; invoked automatically) and **custom skills** (your workflows).
- Skills need **Code execution and file creation** turned on (Settings > Capabilities). Manage them in Customize > Skills.
- You do not call skills by name; Claude picks them from your request and mentions the skill it uses.
- Uploaded files are not edited in place: Claude creates a new version.
- Build a custom skill by chatting: describe the workflow, answer questions, upload references, select **Save skill**. If it does not appear, upload it manually in Customize > Skills.
- Security: install custom skills only from trusted sources and review any external skill first. Skills you upload are private to your account.
- Skills and projects work together, e.g. a skill pulling from a project's knowledge.
