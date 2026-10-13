# Lesson 11: Claude in Action: Use-Cases by Role

- **Course:** Claude 101 (lesson 11 of 13, ~12 min)
- **Source:** https://academy.claude.com/courses/claude-101/claude-in-action-use-cases-by-role
- **Date:** 2026-10-13
- **Status:** In progress

The lesson has no developer-specific use cases, so these exercises apply its general use cases to ReviewRadar. All exercises use ReviewRadar as the topic.

## Sample data (used in Ex 1 and Ex 3)

```
1  | Airport  | 2 | Waited 50 minutes, nobody apologized.
2  | Airport  | 2 | Front desk understaffed, queue out the door.
3  | Airport  | 3 | Doctor was great but check-in was slow.
4  | Airport  | 1 | Billing mistake and nobody called back.
5  | Downtown | 5 | Friendly staff, quick visit.
6  | Downtown | 4 | Clean and efficient.
7  | Downtown | 3 | Parking is expensive.
8  | Riverside| 4 | Good care, parking is hard.
9  | Riverside| 5 | Best clinic experience I've had.
10 | Riverside| 2 | Phone line always busy, could not book.
```

## Exercises

### Ex 1: Analyze patterns in user feedback

**Where:** Claude.ai (regular chat)

**Initial prompt:**
```
Analyze these reviews.

(paste the sample data)
```
**Link:**

**Improved prompt** (new chat):
```
You are helping the owner of a 3-branch clinic chain decide where to invest first. Analyze these reviews (id | branch | rating | text). Output: (1) the top 3 complaint themes with the review ids behind each, (2) one strength to protect, (3) the branch needing action first and why, (4) one recommended action per theme. Do not invent reviews or numbers. Keep it under 200 words.

(paste the sample data)
```
**Link:**

### Ex 2: Generate a project status report

**Where:** Claude.ai (regular chat)

**Initial prompt:**
```
Write a status report for my project.
```
**Link:**

**Improved prompt** (new chat):
```
Create a one-page status report as an artifact for my mentor, who reviews my 15-day Claude Code training lab. Project: ReviewRadar, a Django app that classifies review sentiment with the Claude API. Done so far: Django project skeleton, Claude 101 lessons 2 to 10 with notes and exercises. Not started: models, services, tests, capstone. Sections: summary (2 lines), done, in progress, risks, next 3 days. Plain language, no more than 200 words. Mark anything you had to assume.
```
**Link:**

### Ex 3: Verify statistics from raw data

**Where:** Claude.ai (regular chat, code execution on)

**Initial prompt:**
```
Are my averages right? Airport 2.0, Downtown 4.0, Riverside 4.0, overall 3.0.

(paste the sample data)
```
**Link:**

**Improved prompt** (new chat):
```
Verify these claims using the data below. Compute each average with code, show the calculation, and give a verdict (correct or incorrect, with the right value) for each claim. Claims: Airport average 2.0; Downtown average 4.0; Riverside average 4.0; overall average 3.0. Do not trust my numbers.

(paste the sample data)
```
**Link:**

Self-check: Airport and Downtown are right. Riverside is actually 3.67 and overall is 3.1.

### Ex 4: Map use cases to your work

**Where:** thinking exercise, no chat needed

Browse the Use Case Gallery linked in the lesson and pick 3 use cases you could try now.

| Use case | Where it fits ReviewRadar | First prompt to try |
|----------|---------------------------|---------------------|
| | | |
| | | |
| | | |

## Key takeaways

- Claude fits any role; each use case in the lesson links to a step-by-step guide in the **Use Case Gallery**.
- General use cases: project status reports, analyzing patterns in user feedback, packaging brand guidelines in a skill.
- Role examples: Sales (battle cards, deal prep, reports), Marketing (campaign analysis, content adaptation), Finance (models, investment memos, inherited spreadsheets), HR (onboarding guides), Legal (discovery timelines), Research (literature review, verifying statistics).
- The lesson has no developer use cases: adapt the general ones to your work, e.g. feedback analysis becomes review analysis.
- Try 2-3 use cases from your own role, then browse the gallery for more.
- Verify numbers yourself: ask Claude to compute with code and show its work.
