# Lesson 2: A CLAUDE.md that follows

- **Course:** Claude Code in action (lesson 2 of 9, ~7 min)
- **Source:** https://academy.claude.com/courses/claude-code-in-action/a-claude-md-that-follows
- **Date:** 2026-10-20
- **Status:** In progress

The lesson has no exercises of its own. These exercises are written for this lab and use the ReviewRadar memory files. Run them in Claude Code, folder `claude-code-training-lab`. They are audits and proposals: do not apply any change to `.claude/` or commit. Revert anything by accident with `git checkout .claude`.

## Exercises

### Ex 1: Map the four locations

**Where:** Claude Code, read-only. Run `/memory` or `/context` to see what was loaded.

**Initial prompt:**
```
what CLAUDE.md files do you have?
```

**Improved prompt:**
```
List every memory file loaded in this session, grouped as managed policy, user, project and local. For each: the path, the number of lines, and one line on what it holds. Then say which of them I can change and which a team mate would see after a git pull.
```

| Location | Path in this setup | Lines | Shared through git? |
|---|---|---|---|
| Managed policy | | | |
| User | `~/.claude/CLAUDE.md` | | |
| Project | `.claude/CLAUDE.md` | | |
| Local | (`CLAUDE.local.md`, git-ignored) | | |

| Question | Your answer |
|---|---|
| Where does a personal preference (for example answering in Vietnamese) belong? | |
| Where does a team rule (for example the branch name format) belong? | |
| Is `CLAUDE.local.md` ignored by git here? (check `.gitignore`) | |

### Ex 2: Hard rules or guidance?

**Where:** Claude Code, read-only.

**Prompt:**
```
Read .claude/CLAUDE.md, .claude/rules/*.md, .claude/settings.json and the hooks in .claude/hooks/. List every rule that says "never" or "always" or "must not". For each, say whether it is only advice in text, or also enforced by a hook or a permission rule (name the hook or the line). Output a table: rule | where it is written | enforced by | gap.
```

Fill the table from the answer and check two rows by hand (open the hook).

| Rule | Written in | Enforced by | Gap? |
|---|---|---|---|
| Never commit directly to `main` | | | |
| No `Co-Authored-By` or "Generated with" line | | | |
| One GitHub repository only | | | |
| Never push without approval | | | |
| Never read, print or write the token | | | |
| Never merge a pull request | | | |

**Decide:** for each gap, is a hook worth it, or is guidance enough? Write the reason in one line. Rule of thumb from the lesson: if breaking it once is costly and the action can be detected before it runs (a pre-tool-use hook), it is a hook.

### Ex 3: Imports versus context cost

**Where:** Claude Code, read-only.

1. Run `/context` and write down how much the memory files take.
2. Open `.claude/CLAUDE.md` and find the `@context/...` lines.
3. Prompt:
```
Which parts of what you loaded at the start come from @imports and which are written in CLAUDE.md itself? If I moved the "Available skills" table into a separate file with @import, would the context shrink? Explain, then say what would actually shrink it.
```

| Question | Your answer |
|---|---|
| Does an `@import` reduce the context? (expected: no, it loads up front) | |
| What does reduce the context? (expected: remove the lines, or move them to a skill or a file read only on demand) | |
| Which file in this project is "referenced, not auto-loaded" on purpose? (see `knowledge/` in CLAUDE.md) | |

### Ex 4: Rewrite five rules to be specific and checkable

**Where:** Claude Code or on paper. Rewrite only; do not edit the files.

Rewrite each weak rule so a person could check it with a yes or no. Name the replacement when you ban something.

| Weak rule | Your rewrite | Check (yes or no) |
|---|---|---|
| Follow best practices for views | | |
| Don't use signals | (hint: say what to use instead; see `~/.claude/CLAUDE.md`) | |
| Write good tests | | |
| Keep functions small | | |
| Be careful with rounding | (hint: name the function) | |

Examples from the lesson to copy the shape from:
- "Follow best practices for API routes" becomes "Put new API routes in `src/api/handlers`, one per file."
- "Don't use default exports" becomes "Use named exports, not default exports."

Then ask Claude to grade your five rewrites:
```
Grade each rewrite: is it specific, can it be checked with yes or no, does it name the replacement? Give one improvement per rule. Do not edit any file.
```

### Ex 5: Emphasis budget

**Where:** Claude Code, read-only.

**Prompt:**
```
Count the words IMPORTANT, MUST, NEVER, ALWAYS, YOU MUST (any case) in .claude/CLAUDE.md and .claude/rules/*.md. Show file, line and the rule for each. Then rank the rules by how much it would hurt if each were broken once, and tell me which two or three deserve emphasis and which should be written in a normal voice.
```

| Question | Your answer |
|---|---|
| How many emphasized lines are there? | |
| Which two or three rules hurt most when broken? | |
| Which emphasized lines would you make quieter? | |

### Ex 6: Prune with a justification for every line

**Where:** Claude Code, read-only. Proposal only.

**Prompt:**
```
Treat .claude/CLAUDE.md as production code. For each section, answer "if I delete this, what mistake would Claude make?". Output a table: section | lines | mistake if deleted | keep, move to a skill, move to a rule, move to a hook, or delete. Do not edit any file. End with the line count before and after if every proposal were applied.
```

| Section | Lines | Mistake if deleted | Decision |
|---|---|---|---|
| Quick orientation | | | |
| Where things live | | | |
| Mandatory rules table | | | |
| Persistent knowledge table | | | |
| Where knowledge lives, artifacts | | | |
| AI engineering lifecycle | | | |
| Working with helpers | | | |
| Available skills | | | |
| Available commands | | | |
| A short request | | | |
| MCP and permissions | | | |
| Removed, and why | | | |

Keep the answer as a proposal. Choosing what to cut is a separate task with its own plan and approval.

### Ex 7: Treat a mistake as a bug against CLAUDE.md

**Where:** Claude Code. Revert afterwards.

1. Ask for something that the rules cover but tempts a shortcut:
```
Commit the current changes now with a short message.
```
(There should be none; make a trivial change first, such as a space in a docstring.)
2. Watch what happens: does the hook stop it, does Claude ask for the Gate 2 OK, does the message follow `rules/git.md`?
3. If Claude got something wrong, do **not** fix it by hand. Say:
```
add that to the CLAUDE.md file
```
and read the proposed line. Check it with the three tests: specific, checkable, names the replacement. Decline the edit.

| Question | Your answer |
|---|---|
| What stopped or shaped the commit: the hook, the rule text, or Claude's own judgment? | |
| If you had to add one line, what would it say? | |
| Would that line be better as a hook? | |

### Ex 8: Paper exercise, where does each rule go?

| # | Rule | CLAUDE.md, import, skill, hook or local | Reason |
|---|---|---|---|
| 1 | Never push to main | | |
| 2 | Use `uv run pytest -q --no-cov` for a quick test run | | |
| 3 | The steps to publish an issue on GitHub (preview, labels, approval) | | |
| 4 | Answer me in Vietnamese | | |
| 5 | Scores are rounded half up, with `rounded_average` | | |
| 6 | My own scratch notes for this repository | | |
| 7 | Block any command that prints the token | | |

Expected: 1 hook (pre-tool-use); 2 CLAUDE.md (a command Claude cannot guess); 3 skill; 4 user file (`~/.claude/CLAUDE.md`); 5 CLAUDE.md or a rule file, because it applies broadly; 6 local file (`CLAUDE.local.md`); 7 hook.

## Key takeaways

- **CLAUDE.md is guidance, not enforced configuration.** Every line competes for Claude's attention, so a leaner file is followed more reliably.
- **Ask first whether CLAUDE.md is the right tool.** Hard lines ("never push to main") belong in a **pre-tool-use hook**, which runs before the action and can block it. Conventions belong in CLAUDE.md.
- **Four locations, all loaded together and stacked:** managed policy (organization, cannot be excluded), user (personal, all projects), project (shared in git), local (git-ignored, personal, one repository).
- **Imports organize, they do not save context.** `@.claude/conventions/code-style.md` splits a big file, but everything still loads at launch.
- **Phrasing makes rules stick:**
  - Be **specific and checkable**: "Put new API routes in `src/api/handlers`, one per file", not "follow best practices".
  - **Name the replacement**: "Use named exports, not default exports", not just "don't use default exports".
  - **Emphasis is a budget**: IMPORTANT and YOU MUST work only against quieter rules. Keep them for the two or three rules that hurt most.
- **Keep the file under revision.** A wrong behavior is a bug report against CLAUDE.md. Say "add that to the CLAUDE.md file" instead of fixing it by hand each time.
- **Bottom line:** treat CLAUDE.md like production code and delete any line you cannot justify. Move hard rules to hooks, organize with imports, make rules specific, spend emphasis rarely, revise after every mistake.
