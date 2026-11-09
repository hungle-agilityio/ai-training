"""#366: one pull request per epic from its branch into main (spec epic-review-once)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from ops import epic_branch
except ImportError:  # run as a script from ops/
    import epic_branch  # type: ignore[import-not-found,no-redef,unused-ignore]

IN_EPIC = "agent:in-epic"
EPIC_TITLE_PREFIX = re.compile(r"^\s*epic\s*:\s*", re.IGNORECASE)
REPORT = re.compile(r"https://claude\.ai/artifact/[^\s)>\]]+")
CLOSES = re.compile(r"Closes #(\d+)")
PULL_URL = re.compile(r"/pull/(\d+)")


def labels_of(item: dict[str, Any]) -> set[str]:
    return {label["name"] for label in item.get("labels") or []}


def title_for(epic: dict[str, Any]) -> str:
    return "[EPIC] " + EPIC_TITLE_PREFIX.sub("", str(epic.get("title") or "")).strip()


def row_for(task: int, branch: str, prs: list[dict[str, Any]]) -> str:
    """One table row, from the newest pull request of the task merged into the epic branch."""
    merged = [
        p
        for p in prs
        if p.get("state") == "MERGED"
        and p.get("baseRefName") == branch
        and CLOSES.search(p.get("body") or "")
        and int(CLOSES.findall(p.get("body") or "")[0]) == task
    ]
    if not merged:
        return f"| #{task} | — | — |"
    newest = max(merged, key=lambda p: p["number"])
    found = REPORT.search(newest.get("body") or "")
    return f"| #{task} | #{newest['number']} | {found.group(0) if found else '—'} |"


def body_for(
    marker: str, epic: int, branch: str, tasks: list[int], prs: list[dict[str, Any]]
) -> str:
    rows = [row_for(task, branch, prs) for task in tasks]
    closing = [f"Closes #{task}" for task in tasks] + [f"Closes #{epic}"]
    lines = [marker, "", "| Task | Pull request | Verify report |", "|---|---|---|", *rows]
    return "\n".join([*lines, "", *closing]) + "\n"


def with_line(body: str, epic: int, task: int) -> str:
    """The task's `Closes` line goes just above the epic's, the last of the list."""
    line = f"Closes #{task}"
    last = re.compile(rf"^Closes #{epic}\b", re.MULTILINE)
    if last.search(body):
        return last.sub(f"{line}\nCloses #{epic}", body, count=1)
    return f"{body.rstrip()}\n{line}\n"


class EpicPullRequests:
    """One tick's work on the epic pull requests; `tick` is the agent_tick.Tick."""

    def __init__(self, tick: Any, repo_root: Path, marker: str) -> None:
        self.tick = tick
        self.root = repo_root
        self.marker = marker

    def keep(self, prs: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
        """AC1, AC5: one failure is one log line and never stops the other epics."""
        for epic in sorted(issues, key=lambda i: i["number"]):
            if "epic" not in labels_of(epic):
                continue
            try:
                self.one(epic, prs, issues)
            except (RuntimeError, ValueError) as error:
                self.tick.say(f"epic #{epic['number']}: {error}; next tick")

    def one(
        self, epic: dict[str, Any], prs: list[dict[str, Any]], issues: list[dict[str, Any]]
    ) -> None:
        number = epic["number"]
        branch = epic_branch.branch_name(number, epic.get("title") or "")
        tasks = sorted(
            (i for i in issues if epic_branch.epic_number(i.get("body") or "") == number),
            key=lambda i: i["number"],
        )
        opened = next(
            (
                p
                for p in prs
                if p["state"] == "OPEN"
                and p.get("headRefName") == branch
                and p.get("baseRefName") == "main"
            ),
            None,
        )
        if opened is not None:
            self.add_lines(opened, number, [t["number"] for t in tasks if IN_EPIC in labels_of(t)])
            return
        if not tasks or any(IN_EPIC not in labels_of(t) for t in tasks):
            return
        if self.open_on_github(branch):
            return
        if not self.has_main(branch):
            self.tick.say(f"epic #{number}: pull request waits, {branch} does not have main")
            return
        self.open(epic, branch, [t["number"] for t in tasks], prs)

    def open_on_github(self, branch: str) -> bool:
        """An open pull request the loop's list does not show, the owner's own for example."""
        found = self.tick.gh_json(
            "pr", "list", "--head", branch, "--base", "main", "--state", "open", "--json", "number"
        )
        return bool(found)

    def has_main(self, branch: str) -> bool:
        ancestor = ["merge-base", "--is-ancestor", "origin/main", f"origin/{branch}"]
        code, _ = self.tick.host.run(["git", "-C", str(self.root), *ancestor])
        return bool(code == 0)

    def write_body(self, number: int, body: str) -> Path:
        path = self.tick.home / f"epic-pr-{number}.md"
        path.write_text(body)
        return Path(path)

    def open(
        self, epic: dict[str, Any], branch: str, tasks: list[int], prs: list[dict[str, Any]]
    ) -> None:
        number = epic["number"]
        path = self.write_body(number, body_for(self.marker, number, branch, tasks, prs))
        code, out = self.tick.gh(
            "pr", "create", "--base", "main", "--head", branch,
            "--title", title_for(epic), "--body-file", str(path),
        )  # fmt: skip
        if code != 0:
            first = epic_branch.first_line(out)
            self.tick.say(f"epic #{number}: pull request not opened ({first}); next tick")
            return
        match = PULL_URL.search(out)
        new = match.group(1) if match else "?"
        self.tick.say(f"epic #{number}: opened PR #{new} into main")
        self.tick.notify(f"Epic #{number} is ready for your review: PR #{new}")

    def add_lines(self, pr: dict[str, Any], epic: int, tasks: list[int]) -> None:
        """AC5: a task that reached the epic branch after the pull request was opened."""
        body = str(pr.get("body") or "")
        have = {int(n) for n in CLOSES.findall(body)}
        missing = [task for task in tasks if task not in have]
        if not missing:
            return
        for task in missing:
            body = with_line(body, epic, task)
        path = self.write_body(epic, body)
        code, out = self.tick.gh("pr", "edit", str(pr["number"]), "--body-file", str(path))
        if code != 0:
            first = epic_branch.first_line(out)
            self.tick.say(f"pr-{pr['number']}: Closes lines not added ({first}); next tick")
            return
        pr["body"] = body
        listed = ", ".join(f"#{task}" for task in missing)
        self.tick.say(f"pr-{pr['number']}: Closes lines added for {listed}")
