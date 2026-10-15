---
name: pr-review
description: Review a merge request or a branch and write one review in a fixed structure (PR Review Summary, Strengths, Issues & Recommendations), in English, ready to paste into the merge request. Use when the user asks to review a PR or MR, review a branch, "give me review comments", or play the role of another reviewer. Read-only: it never posts, approves or merges.
---

# PR review

The rules live in `.claude/rules/`, `.claude/knowledge/` and `.claude/CLAUDE.md`. This skill is the procedure and the output format. The result is **one document, in English**, that the user pastes into the merge request by hand.

## Safety rules

- Read-only. Never change code, tickets or branches, never switch the user's branch, never touch `db.sqlite3`. To run the checks on another branch, use a temporary `git worktree` in the scratchpad and remove it afterwards.
- Never post a comment, approve or merge on GitLab. The user posts the review. This follows `.claude/CLAUDE.md`: Claude never merges or approves.
- Never open files named `*DO-NOT-OPEN*`.
- Report only what you verified. A claim you did not check (production timing, a browser, a test you did not run) is written as "not verified", never as a fact. Do not invent strengths to fill a category.

## 1. Find what to review

1. The branch or merge request the user names. If none, use the current branch.
2. The target is the merge request target; if the user does not say, it is `feat/claude-code-training-lab` (the base of the project, `main` has no code yet). Diff with `git diff <target>...<branch>` and read the commits with `git log <target>..<branch>`; use `git show <branch>:./<path>` to read files without switching branches.
3. The ticket: the issue number from the branch name (`bug/1-...` is `#1`), then its `docs/issues/<type>/<name>/04-final.md` and the index `docs/issues/README.md`. Check the change against the ticket's expected result. Use GitLab issue numbers in the review, not local numbers.

## 2. Review order

Go through the checklist in this order, and stop adding findings once the three most important are clear:

1. **Correctness:** does it do what the ticket asks; edge cases (empty data, zero, boundaries); behaviour that changed for callers, for example an API value that can now be empty.
2. **Tests:** is every acceptance criterion tested; was the test written to fail first; do the tests assert the real thing (query counts, exact values), not only "no error".
3. **Readability:** naming, duplication, dead code left behind, comments that are wrong or use outdated ticket numbers.
4. **Security basics:** input validated with forms, output escaped, no secrets or personal data in logs, no raw SQL.
5. **Scope:** only what the ticket asks; unrelated changes; overlap and expected conflicts with other open branches.

Project rules to check (from `.claude/CLAUDE.md`, `.claude/rules/`, `.claude/knowledge/KNOWN_PITFALLS.md` and the global standards): logic in the service layer and a thin view; type hints and `mypy`; N+1 is a blocker and the query count is asserted; the rounding rule (half up through `rounded_average`, test the type); pagination order has a unique tiebreaker; the time zone is `Asia/Ho_Chi_Minh`; 90% coverage on services; the commit format and `Part of #<id>`.

Run `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` on the branch (in a worktree if it is not checked out) and report the real result. Failing tests that belong to other open tickets are named, not hidden.

## 3. Output format

Write exactly this structure, in English, as one markdown document. Do not add other sections.

```markdown
## PR Review Summary

This PR addresses ticket **#<id>** ("<ticket title>"). <One or two sentences: the problem and why it matters.> The PR:

1. **<Change>** - <what it does>
2. **<Change>** - <what it does>
3. **<Change>** - <what it does>

**Verdict: <Approve | Approve with comments | Request changes>.** <One sentence why. Say which issues should be fixed before merging.>

---

## Strengths

**Security Improvements:**

- <only what is true; if nothing changes, say "No security impact, and none claimed: ...">

**Architecture:**

- ...

**Performance:**

- <numbers before and after when measured; say when they come from a simulation>

**Testing:**

- ...

**Maintainability:**

- ...

---

## Issues & Recommendations

### 1. <Short title of the problem>

`<file>:<line>` (or the page or the description)

<What is wrong and what the user or developer sees. Add a short code block when it makes the problem clear.>

**Recommendation:** <the concrete change, or the choice between two changes>

### 2. <Title>
...

### 3. <Title>
...
```

Rules for the format:

- **Summary:** at most **3** numbered items, even if the diff does many things; group related changes under one item. The verdict is one of the three words.
- **Strengths:** use the categories above (add or drop a category such as Testing or Maintainability when it fits), each with short bullets, names in `code` format. Keep only categories that have something true to say, but keep Security Improvements and say "No security impact" when that is the case.
- **Issues & Recommendations:** at most **3** issues, the three that matter most, ordered by importance. Each has a numbered heading, where it is (file and line, or "MR description"), what is wrong, and a **Recommendation**. Say in the heading text or the first line whether it should be fixed before merging or is a suggestion. Nits and lesser findings are left out of the document; tell the user in the chat answer how many were left out and offer them.
- Mention what was not verified (production timing, browsers, tests not run) in the Summary verdict or in the matching strength or issue, not in a separate section.
- The tone is that of a colleague: specific, short, no blame, and no praise that is not backed by the diff.

## 4. Answer format

Give the review document first, complete and ready to paste. After it, in the user's language, add at most three short lines: what you ran (tests, lint, worktree), what you did not verify, and how many lesser findings you left out. Nothing was posted to GitLab.
