# Lesson 3: Getting Better Results

- **Course:** Claude 101 (lesson 3 of 13, ~10 min)
- **Source:** https://academy.claude.com/courses/claude-101/getting-better-results
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic and are done in regular Claude.ai chats.

## Exercises

### Ex 1: Too generic

**Initial prompt:**
```
Write an email about the review results.
```
**Link:** https://claude.ai/share/4283f724-d5f4-4c72-abe7-0e00a2104fc0

**Improved prompt:**
```
Write an email to the owner of a 3-branch clinic chain (Downtown, Riverside, Airport). Reason: the Airport branch's average rating dropped from 4.6 to 3.8 in the last two weeks, mostly because of waiting-time complaints. This is the second dip this quarter. Goal: get approval to add one receptionist at Airport. Tone: direct and respectful, no jargon. Length: 120 words max.
```
**Link:** https://claude.ai/share/870cfb03-6610-4067-aabb-48b673bd90de

### Ex 2: Format and tone

**Initial prompt:**
```
Summarize these reviews: "Great service, will come back!", "Waited 50 minutes and nobody apologized.", "Staff was friendly but parking is a nightmare."
```
**Link:** https://claude.ai/share/d3a826b1-4c03-47ee-99ec-50f5d8d85cdd

**Improved prompt:**
```
Summarize these reviews: "Great service, will come back!", "Waited 50 minutes and nobody apologized.", "Staff was friendly but parking is a nightmare."

Format: a table with columns Review | Sentiment | Main topic, followed by one bolded sentence with the overall takeaway. Example row: | "Food was cold" | Negative | Quality |
Tone: plain and neutral, like an internal ops report. Max 80 words outside the table.
```
**Link:** https://claude.ai/share/fbdc9a55-b052-410e-8741-c9ba1e983e1c

### Ex 3: Confident but wrong

Check the cited URL yourself: do the numbers match?

**Initial prompt** (web search off):
```
What are the exact rate limits and per-token prices of the Claude API for Sonnet 5.5?
```
**Link:** https://claude.ai/share/befb701d-fde4-4197-9e28-d962a4dd522f

**Improved prompt** (web search on):
```
What are the exact rate limits and per-token prices of the Claude API for Sonnet 5.5? Search the official Anthropic docs, cite the source URL for each number, and tell me your confidence level for each. If you cannot verify a number, say so instead of guessing.
```
**Link:** https://claude.ai/share/a98c78a1-8532-4796-a951-ac30e37714b4

### Ex 4: Mini eval (delegation-diligence loop)

Score each run against the table below (x/6 correct).

Ground truth I labeled myself:

| # | Review | Expected |
|---|--------|----------|
| 1 | "Great service, will come back!" | positive |
| 2 | "Waited 50 minutes and nobody apologized." | negative |
| 3 | "Oh great, another 'quick' appointment that took an hour. Love that." | negative (sarcasm) |
| 4 | "The staff was friendly but the parking is a nightmare." | mixed |
| 5 | "Appointment was at 3pm. I was seen at 3:10." | neutral |
| 6 | "Không có gì để chê, bác sĩ rất tận tâm." | positive |

**Initial prompt:**
```
Classify the sentiment of each review.

1. "Great service, will come back!"
2. "Waited 50 minutes and nobody apologized."
3. "Oh great, another 'quick' appointment that took an hour. Love that."
4. "The staff was friendly but the parking is a nightmare."
5. "Appointment was at 3pm. I was seen at 3:10."
6. "Không có gì để chê, bác sĩ rất tận tâm."
```
**Link:** https://claude.ai/share/ca4a5d25-c207-4222-9fb0-1981aa6bc24c

**Improved prompt** (open a new chat, add definitions and examples):
```
Classify the sentiment of each customer review for a clinic. Labels: positive, negative, neutral, mixed.
Definitions: mixed = contains both clear praise and clear complaint. Sarcasm counts as the sentiment it implies, not the literal words. Reviews may be in English or Vietnamese.
Output: a table with columns # | Label | One-line reason.
Example: "Food was great but slow" -> mixed, praise for food and complaint about speed.

1. "Great service, will come back!"
2. "Waited 50 minutes and nobody apologized."
3. "Oh great, another 'quick' appointment that took an hour. Love that."
4. "The staff was friendly but the parking is a nightmare."
5. "Appointment was at 3pm. I was seen at 3:10."
6. "Không có gì để chê, bác sĩ rất tận tâm."
```
**Link:** https://claude.ai/share/2659b245-d541-4afd-ad60-9b68171e780c

## Key takeaways

- Unexpected output is a signal to refine, not a failure. Diagnose first:
  - Generic: add audience, role, constraints.
  - Wrong length: state it explicitly.
  - Wrong format: show an example or describe the structure.
  - Confident but wrong: verify, ask for sources and confidence, enable web search.
  - Wrong tone: describe it or give a writing sample.
- Treat the first draft as a starting point. Give specific feedback ("cut the second paragraph"), not vague ("make it better"). If a chat has drifted, start fresh.
- 4D Framework: Delegation, Description, Discernment, Diligence. Lesson 2's stage/task/rules is Description; troubleshooting is Discernment and Diligence.
- Evals: gather 5-10 real examples with known-correct answers, prompt Claude, compare, refine, retest. Decide what to delegate and what needs human review.
- Validation builds confidence but you stay accountable for the result.
