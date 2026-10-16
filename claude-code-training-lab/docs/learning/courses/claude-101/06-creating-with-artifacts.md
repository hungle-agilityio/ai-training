# Lesson 6: Creating with Artifacts

- **Course:** Claude 101 (lesson 6 of 13, ~10 min)
- **Source:** https://academy.claude.com/courses/claude-101/creating-with-artifacts
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic and are done on Claude.ai.

## Exercises

### Ex 1: Request the deliverable, not just the content

**Where:** Claude.ai (inside the "ReviewRadar Learning Lab" Project or a regular chat)

**Initial prompt:**
```
Summarize the review trends for each branch.

Airport | Oct 1 | 2 stars | Waited 50 minutes, nobody apologized.
Airport | Oct 4 | 2 stars | Understaffed front desk, long queue.
Airport | Oct 9 | 3 stars | Doctor was great but check-in was slow.
Downtown | Oct 2 | 5 stars | Friendly staff, quick visit.
Downtown | Oct 7 | 4 stars | Clean and efficient.
Riverside | Oct 3 | 4 stars | Good care, parking is hard.
Riverside | Oct 8 | 5 stars | Best clinic experience I've had.
```
**Link:**

**Improved prompt** (new chat):
```
Draft a one-page branch review report as a doc I can share with the clinic owner. Create this as an artifact. Sections: summary, per-branch trend, top complaint, recommended action. Keep it under 250 words, plain language.

Airport | Oct 1 | 2 stars | Waited 50 minutes, nobody apologized.
Airport | Oct 4 | 2 stars | Understaffed front desk, long queue.
Airport | Oct 9 | 3 stars | Doctor was great but check-in was slow.
Downtown | Oct 2 | 5 stars | Friendly staff, quick visit.
Downtown | Oct 7 | 4 stars | Clean and efficient.
Riverside | Oct 3 | 4 stars | Good care, parking is hard.
Riverside | Oct 8 | 5 stars | Best clinic experience I've had.
```
**Link:**

After the artifact appears, try all three ways to edit: type a change directly, leave a comment on one passage for Claude, and ask for one revision in the conversation.

### Ex 2: Interactive dashboard

**Where:** Claude.ai (works on any plan)

**Initial prompt:**
```
Make a dashboard for reviews.
```
**Link:**

**Improved prompt** (new chat):
```
Build an interactive dashboard as an artifact for a clinic owner who is not technical. Use this data: Airport ratings 2, 2, 3; Downtown ratings 5, 4; Riverside ratings 4, 5. Show the average rating per branch as a bar chart, highlight any branch below 3.5 in red, and add a dropdown to filter by branch. Keep the design clean, one screen, no scrolling.
```
**Link:**

### Ex 3: Turn a doc into a deck

**Where:** Claude.ai (same chat as the Ex 1 improved prompt). Slides is in beta; if it is not available, skip this exercise.

**Initial prompt:**
```
Turn this into slides.
```
**Link:**

**Improved prompt** (new message in the same chat, or a copy of it):
```
Turn the report into a five-slide deck for the monthly owner meeting. Slide 1: title and one-line headline. Slide 2: ratings per branch. Slide 3: top complaint with one quote. Slide 4: recommended action. Slide 5: next steps with an owner and a date for each. Create this as an artifact.
```
**Link:**

## Key takeaways

- An artifact is a **finished output** (doc, deck, design, dashboard, prototype) that opens in its own window next to the chat. Request it explicitly: "Create this as an artifact."
- **Request the deliverable, not just the content.** "Summarize" gives a chat reply; "a one-page doc I can share" gives an artifact.
- Be specific and **describe the end user** so Claude can make design choices.
- Three ways to edit, combinable: **edit directly**, **comment** on a specific element, **ask in the conversation**.
- Create the artifact **late in the conversation**, after Claude understands the problem.
- Paid plans keep artifacts in the Artifacts tab; on Free, an artifact stays attached to its chat.
- Claude Design, Slides, and Docs are in beta on paid plans. Interactive dashboards, trackers, and flowcharts work on every plan.
- Artifacts are private by default. Share with named people (view, comment, edit) or a link. Only the artifact is public, not the conversation.
- Exports: decks to .pptx or .pdf, designs to .pptx, .pdf, or .html, docs to Google Docs or .docx.
- Embedded doc charts are snapshots: ask Claude to refresh data when needed.
