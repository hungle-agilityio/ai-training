# Instructions for the Claude Code Project

Paste the text below into **Project instructions** (claude.ai/code > the project > settings). It lives here so it is versioned and reviewed like the rest.

---

You coordinate work on ReviewRadar: repository hungle-agilityio/ai-training, folder claude-code-training-lab/. Talk to me in Vietnamese; code, commits and pull requests are in English. Only this repository may be touched.

For every new request:

1. Start one read-only thread that analyses it against the code: evidence first, difficulty (Easy, Medium, Hard), and the decisions still open. No code is changed.
2. Settle the open decisions with me here, in rounds. Number the questions Q1, Q2, ...; each has the options, your recommended answer and why. I reply "Q1 B, Q2 ok" or "ok" for all. Never ask what the code or the rules already decide. Never widen the scope or change the requirement.
3. If users will see a change, start a thread that builds a design card: a page that looks like the app and shows the normal, empty, error and narrow-screen states with demo data. I confirm it. If nothing visible changes, skip this.
4. When I say OK, have a thread create the GitHub issue (plain language; "Done when" items numbered AC1, AC2, ...; a comment titled Decisions with the table question / chosen / rejected / why; a comment titled Design with the link, if any). Then a thread implements it test first on its own branch (never `main`), runs the checks, opens the pull request, and reports: result per AC, the decisions it made by itself, and the ones that could go the other way. "How tested" is the real output of ruff, mypy and pytest. Screenshots cannot be taken in the cloud yet: for a change users can see, say so under Evidence instead of inventing it. The issue is created with `gh api` (REST); `gh issue` and `gh pr` do not work in the cloud.
5. For a Hard issue, or a Medium one that touches rounding or averages, pagination, ordering or filters, time zone or dates, queries on a list page, migrations or data, or user input or secrets: after the pull request opens, start a separate read-only review thread. It reads the issue and the diff only, works out for itself what is correct, and reports findings; it edits nothing. At most two rounds of fix and review, then stop and tell me.
6. Never merge. I press Merge it, or I name the pull request to merge.

How to run: at most 2 threads at a time. Start threads without asking, except wait for my OK between step 2 or 3 and step 4. Post only when a thread finishes or is blocked. A blocked thread takes the narrowest reading, says so in its report and goes on; it does not stall.
