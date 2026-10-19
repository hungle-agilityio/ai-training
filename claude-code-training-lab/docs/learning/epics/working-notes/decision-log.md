# Decision log of the Claude Code practices epics

Decisions taken with the user on 2026-10-16. The codes P01 to P43 are the old problem codes; `slides-coverage.md` maps them to the tasks.

### Decisions of the first grill-me (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D1 | Where drafts live until created | `docs/learning/issues/<type>/<name>.md`, same layout as app issues, with its own index |
| D2 | After creation on GitHub | The file is kept as the approved text with the number in the index; GitHub holds status; the file is not edited again, changes go to GitHub comments |
| D3 | Approval unit | The whole epic in one go: a table (title, labels, one-line summary), the user may open any draft and drop single rows; exact items are named, so Gate 3 holds |
| D4 | Epic on GitHub | One parent issue labelled `epic`; sub-tasks linked as sub-issues if GitHub allows (tested in P43), otherwise a checklist in the parent. No project board for now |
| D5 | Work already done locally (P01, P02, P14, docs split, one-file issues) | One combined issue "Phase 0", created and closed after merge, so branch and commits carry a number |
| A1 | Assumption: labels | Same names as the `write-issue` rule (`task`, `epic`, area labels, `needs-info`...), no `type::` style |
| A2 | Assumption: codes | P01 to P43 live only in the epic table beside the real `#N`, never in issue titles |

### Decisions of the grill-me on P43 (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D6 | Way to talk to GitHub | The official GitHub MCP server, remote address, signed in with a fine-grained token that is limited to this one repository. `gh` stays installed for manual use |
| D7 | Account that owns the private repository | `hungle-agilityio` (the account known to `gh` on this machine; its login token is expired and must be renewed) |
| D8 | Creating issues after the epic is approved (D3) | Allowed without asking again: read, create and edit issues, comments, labels, sub-issue links. Ask for anything else. Denied: merge, delete, close an issue Claude did not finish, change repository settings |
| D9 | How the connection is tested | Read-only checks first (repository, labels), then the first two real issues, "Phase 0" (D5) and the epic parent issue; the link between them tests sub-issues. If sub-issues fail, use a checklist in the parent |
| A3 | Assumption: token | An environment variable; `.mcp.json` only names the variable; Claude never reads or prints it and never writes it to a file |
| A4 | Assumption: shared file | `.mcp.json` is committed (no secret in it) and the GitLab entry is removed |
| A5 | Assumption: pushing code | Still goes through SSH keys and still asks each time; it does not use this token |
| A6 | Assumption: sign-in | The user types `! gh auth login -h github.com` in this session when asked |

### Decisions of the grill-me on P34 and P05 (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D10 | History | Keep the whole history of the lab folder (37 commits, folder prefix removed) and rewrite the old GitLab references `#1`, `#2`, `#4` in commit messages to `GitLab #1`, `GitLab #2`, `GitLab #4`, so they do not link to the wrong GitHub issues |
| D11 | Author in old commits | Rewrite to the GitHub no-reply address of `hungle-agilityio` (exact address taken from the GitHub email settings), and set the same address for new commits in this repository |
| D12 | Repository name | `ai-training` |
| D13 | Old repository | Mirror backup outside the folder, stash exported with it, then rename the old `.git` to `.git-old-gitlab` (reversible); the lab folder gets its own new `.git`; the parent folder keeps its README and `.claude` but is no longer a repository |
| D14 | The 86 uncommitted changes | The split uses only committed history and becomes `main`; afterwards the "Phase 0" issue (D5) exists, a branch `task/<number>-...` is made in the new repository, all current changes are committed with `Part of #<number>` and go through a pull request. A copy of the working tree is made first |
| A7 | Assumption: branches | Only `main` is published (it holds the full history); the merged bug and feature branches are not pushed |
| A8 | Assumption: first push | The first push of `main` is an import and the single exception to "never commit directly to main" |
| A9 | Assumption: remotes | The new remote is `origin` to GitHub; no GitLab remote in the new repository; the old GitLab project is not touched |
| A10 | Assumption: old worktree | `source-tree-display-40a149` is left alone until the user says so |
| A11 | Assumption: every git step | A concrete plan is shown and approved before each hard-to-undo step (split, rename of `.git`, create repository, push) |

Note on D12: the repository is named `ai-training` while the content is the lab, so a second project cannot share this root; also the local parent folder keeps the same name but stops being a repository.

### Decisions of the grill-me on limiting GitHub access (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D15 | Credentials (amended 2026-10-16) | One fine-grained token limited to `hungle-agilityio/ai-training` for `gh` and the MCP server; the broad `gh` login is logged out afterwards. `git push` and `git pull` stay on the existing SSH key, which the user keeps; because GitHub does not limit that key to one repository, the hook is what stops Claude from pushing, pulling, reading or writing any other repository |
| D16 | Existing repository with an automatic first commit | The user deletes it and creates it again empty (no README, no licence); the token is created after that, because it is tied to the repository |
| D17 | Guard inside Claude Code | A hook that blocks `gh`, `git` and `curl` commands reaching another repository, plus allow, ask and deny lists and a default `GH_REPO`; written and tested 2026-10-16 |
| D18 | Where each rule lives | Token = hard boundary; hook and lists = enforcement; `rules/security.md` and decision records = explanation; the token itself only in an environment variable |
| A12 | Decision by the user: SSH key | The key is NOT removed and stays in use for `git`; only access to other repositories is blocked (by the hook for Claude's commands) |
| A13 | Assumption: limits | The guard stops only commands Claude itself runs through the shell tool. It cannot see what a script run by Claude does inside (for example a Python file calling `gh`), nor commands the user types; those are limited only by the token (API) and not at all for `git` over SSH |
| A14 | Assumption: split email | The ID-based no-reply address `104913131+hungle-agilityio@users.noreply.github.com` replaces the earlier username-only form (step 2 redone and verified) |

Token permissions for the user to set: owner `hungle-agilityio`, only repository `ai-training`; Metadata read; Contents read and write; Issues read and write; Pull requests read and write; no Administration, no Actions; Workflows only when CI is added (P06); expiry 30 to 90 days.

Order inside Phase 1 because of D6: P34 (repository from the lab folder), P05 (remote), then P43 (create the token for that one repository, set the variable, connect, test). The GitHub user name for assignee is `hungle-agilityio` (D7).

## Push policy (confirmed in task T11, 2026-10-19)

| Push | Never push | Decided |
|---|---|---|
| App code, tests, dependency list and lock file | Database file, `.env` files, tokens, keys | Trainer answer-key file in the issues folder: never pushed. No such file exists yet; when one is added it is ignored first |
| Team assistant settings: project map, rules, context, knowledge, commands, skills, agents, shared `settings.json` | Personal assistant settings and personal notes (`settings.local.json`, `CLAUDE.local.md`), memory, session logs | Learning journal: pushed, only while the repository is private |
| GitHub workflow, templates, code owners | Virtual environment, caches, coverage output, `.DS_Store` | Copied course notes (`courses/claude-101`, 11 files): already in the history; not pushed to a public repository until the licence is checked |
| Issues folder, epic, decision records, README | Working copies and scratch files, real customer data | Repository visibility: private |

Check made on 2026-10-19 before the push policy: none of `.env`, `db.sqlite3`, `settings.local.json`, `CLAUDE.local.md`, `.coverage` or `.DS_Store` appears anywhere in the 62 commits of the history.

## Repository layout (decided in task T11, 2026-10-19)

The repository root is `ai-training/` and the code lives in `claude-code-training-lab/`, because later plans and practice projects will sit next to it. The first split (root = the lab folder, as the task text and P34 said) was done and pushed, then reversed the same day: it dropped the folder name and the two first commits. The wrong `.git` is kept in `~/hungle/training/backups/git-split-wrong-2026-10-19`; the old GitLab `.git` stays as `ai-training/.git-old-gitlab` (excluded from git). Old `#N` GitLab references were rewritten (`Part of #N` lines removed, `#N` in text became `GitLab #N`) and the author address is the GitHub no-reply address.

Process: nothing is pushed without approval of that exact item; one branch per issue and a pull request into main; run verify first; look at the list of staged files before every commit; never force.

## Protecting the repository (task T12, 2026-10-19): partly done

Decision: keep the repository private on the current plan and rely on local discipline; do not pay for a team plan and do not make the repository public for now.

| Part | State | Evidence |
|---|---|---|
| `.github/` at the repository root (GitHub reads it only there) | Done | The checks workflow ran and passed on the first pull request |
| Checks run inside `claude-code-training-lab/` | Done | Same run |
| Code owners file | Done, but it only names the owner; it cannot force a review | `.github/CODEOWNERS` |
| Weekly dependency updates (`uv`, GitHub Actions) | File done | `.github/dependabot.yml` |
| Rule set on `main` (pull request and passing check required, force push and deletion blocked) | **Not configured, blocked by the plan** | GitHub says rule sets are not enforced on a private repository without a team plan; a direct push to `main` was accepted (`1c54fb9..f307546`, an empty commit) |
| Squash merge only, delete branches after merge | Not checked; set in repository settings, which Claude may not change | The first pull request was merged with a merge commit |
| Secret scanning and push protection | **Not configured, blocked by the plan** | Same limit |

Done when (a direct push to `main` is refused): **not met.**

What still protects `main`: the hook `before-commit-check` blocks commits on `main` and the project rules forbid pushing there, but both bind Claude only, not a person. The checks run on every pull request and a human merges.

Revisit when the repository becomes public or moves to a team plan: create the rule set, turn on secret scanning and push protection, repeat the direct push test and record the result.
