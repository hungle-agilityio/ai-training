"""One tick of the loop: tidy ended builds, then start up to AGENT_CONCURRENCY new ones.

Run by `ops/start-loop.sh` every 10 minutes. Spec: specs/loop-concurrency/spec.md (AC1 to AC12).
`python ops/agent_tick.py` runs one tick; `python ops/agent_tick.py run <key> <folder> <prompt>`
is the background wrapper of one build (started by the tick, not by hand).
"""

from __future__ import annotations

import json
import os
import queue
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

REPO = "hungle-agilityio/ai-training"
OWNER = "hungle-agilityio"
MARKER = "<!-- work-queue -->"
LOCK_MAX_AGE = 15 * 60
RUN_LIMIT = 45 * 60
PAUSE_SECONDS = 60 * 60
MAX_TURNS = 80
STARTS = 3
RETRIES = 3
ALL_PR_LIMIT = 100
OPEN_PR_LIMIT = 40
HINT = (
    "If the Artifact tool is listed only as a deferred tool, load it with ToolSearch "
    '(query "select:Artifact") before you decide that it is missing.'
)
LOG_TAIL = 20
SKIP_LABELS = {"agent:running", "agent:review", "agent:failed", "agent:manual"}
PR_LABELS = {"pr:ready-for-review", "pr:changes-requested", "pr:blocked", "pr:ci-failed"}
RED_CI = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}
ALONE_WORDS = ("migrations/", "models.py")
USAGE_LIMIT = re.compile(
    r"usage limit|limit reached|rate_limit|extra_usage|usage_limit|hit your .*limit", re.IGNORECASE
)
LABEL_COLORS = {
    "agent:running": ("FBCA04", "The loop is building this issue"),
    "agent:failed": ("D93F0B", "The loop could not finish this issue; see the comment"),
    "pr:blocked": ("B60205", "the loop cannot go on without the owner; the reason is a comment"),
}
REPO_ROOT = Path(__file__).resolve().parents[2]
NEEDS_YOU = ("pr:blocked", "pr:ci-failed")
APPROVALS = {
    "/merge",
    "merge",
    "lgtm",
    "approved",
    "approve",
    "looks good",
    "look good",
    "ok",
    "duyệt",
    "ship it",
}
REDO_CONFLICT = "/redo merge origin/main into this branch and fix the conflict"
UPDATE_FROM_MAIN = "Merge branch 'main'"
DONE_MARKS = {"rocket", "confused"}
GREEN_CHECKS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
COMMENT_ID = re.compile(r"(?:issuecomment-|discussion_r)(\d+)")
DEPENDS_LINE = re.compile(r"^\W*Depends on\b(.*)$", re.IGNORECASE | re.MULTILINE)
FILES_HEADING = re.compile(r"^##\s+Files likely touched\s*$", re.IGNORECASE | re.MULTILINE)
BULLET_PATH = re.compile(r"^\s*[-*]\s+[^`\n]*`([^`\n]+)`", re.MULTILINE)
LAB_PREFIX = "claude-code-training-lab/"
NTFY_TITLE = "ReviewRadar"
REMINDER_SECONDS = 6 * 3600
SIGNED_OUT_TEXT = "Claude Code is not signed in"
LOW_PRIORITY = re.compile(
    r"(?:ReviewRadar )?(?:started #|working on PR #|waiting: |queue empty, |"
    r"PR #\d+ merged \(#\d+\); main is now )"
)


class Host(Protocol):
    """Everything the tick does outside its own state folder; faked in tests."""

    def now(self) -> float: ...

    def run(self, args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]: ...

    def spawn(self, args: Sequence[str], log: Path) -> int: ...

    def alive(self, pid: int) -> bool: ...

    def notify(self, topic: str, message: str) -> None: ...


class RealHost:
    def now(self) -> float:
        return datetime.now().timestamp()

    def run(self, args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
        done = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
        return done.returncode, done.stdout + done.stderr

    def spawn(self, args: Sequence[str], log: Path) -> int:
        with log.open("ab") as out:
            child = subprocess.Popen(
                list(args), stdout=out, stderr=subprocess.STDOUT, start_new_session=True
            )
        return child.pid

    def alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def notify(self, topic: str, message: str) -> None:
        self.notify_priority(topic, message, "high")

    def notify_priority(self, topic: str, message: str, priority: str) -> None:
        """#167 AC3: every ntfy post carries the title and a priority; the text is unchanged."""
        request = urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=message.encode(),
            headers={"Title": NTFY_TITLE, "Priority": priority},
        )
        try:
            urllib.request.urlopen(request, timeout=10).close()
        except OSError as error:
            print(f"ntfy failed: {error}")

    def slack(self, url: str, message: str) -> bool:
        """Post to a Slack Incoming Webhook; the URL is a secret and is never printed."""
        data = json.dumps({"text": message}).encode()
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(request, timeout=10).close()
        except (OSError, ValueError) as error:
            print(f"Slack post failed ({type(error).__name__})")
            return False
        return True


@dataclass(frozen=True)
class Settings:
    concurrency: int
    ntfy_topic: str
    slack_url: str = ""
    claude_config_dir: str = ""
    claude_entrypoint: str = ""


@dataclass(frozen=True)
class Target:
    key: str
    number: int
    prompt: str
    branch: str = ""
    alone: bool = False
    message: str = ""
    retry: str = ""
    stack_pr: int = 0
    stack_branch: str = ""
    stack_head: str = ""


@dataclass
class Remark:
    """An owner comment on a loop pull request, on its issue, or on one of its lines (#80)."""

    kind: str  # "conversation", "inline" or "issue"
    id: int | None
    body: str
    created: str
    has_summary_mark: bool
    marked: bool | None = None


@dataclass
class Tick:
    host: Host
    home: Path
    settings: Settings
    log: list[str] = field(default_factory=list)
    remarks: dict[int, list[Remark]] = field(default_factory=dict)
    main_red: bool = False
    pull_problem: str = ""
    open_issues: list[dict[str, Any]] | None = None
    not_planned: dict[int, bool] = field(default_factory=dict)
    main_head: str | None = None
    retargeted: set[int] = field(default_factory=set)

    @property
    def runs(self) -> Path:
        return self.home / "runs"

    def say(self, line: str) -> None:
        self.log.append(line)
        print(line)

    def notify(self, message: str) -> None:
        """ntfy when NTFY_TOPIC is set, Slack when SLACK_WEBHOOK_URL is set (#78 AC6)."""
        if self.settings.ntfy_topic:
            send = getattr(self.host, "notify_priority", None)
            if send is None:
                self.host.notify(self.settings.ntfy_topic, message)
            else:
                send(self.settings.ntfy_topic, message, message_priority(message))
        if self.settings.slack_url:
            post = getattr(self.host, "slack", None)
            if post is None or not post(self.settings.slack_url, message):
                self.say("Slack post failed")

    def gh(self, *args: str) -> tuple[int, str]:
        return self.host.run(["gh", *args, "--repo", REPO])

    def gh_json(self, *args: str) -> Any:
        code, out = self.gh(*args)
        if code != 0:
            raise RuntimeError(f"gh {' '.join(args)} failed: {out.strip()}")
        return json.loads(out)


def message_priority(message: str) -> str:
    """#167 AC1, AC2: information rings silently; everything else, named or not, rings."""
    if SIGNED_OUT_TEXT in message:
        return "urgent"
    return "low" if LOW_PRIORITY.match(message) else "high"


def read_settings(path: Path) -> Settings:
    """Missing file or key: one build at a time, no notifications; a bad number stops the tick."""
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    raw = values.get("AGENT_CONCURRENCY", "1")
    if raw not in {"1", "2", "3"}:
        raise SystemExit(f"AGENT_CONCURRENCY in {path} must be 1, 2 or 3, not {raw!r}")
    return Settings(
        concurrency=int(raw),
        ntfy_topic=values.get("NTFY_TOPIC", ""),
        slack_url=values.get("SLACK_WEBHOOK_URL", ""),
        claude_config_dir=os.path.expanduser(values.get("CLAUDE_CONFIG_DIR", "")),
        claude_entrypoint=values.get("CLAUDE_CODE_ENTRYPOINT", ""),
    )


def claude_env(settings: Settings) -> dict[str, str]:
    """#172 AC1: the Claude Code variables agent.env sets; an empty value sets nothing."""
    pairs = {
        "CLAUDE_CONFIG_DIR": settings.claude_config_dir,
        "CLAUDE_CODE_ENTRYPOINT": settings.claude_entrypoint,
    }
    return {key: value for key, value in pairs.items() if value}


def signed_in(tick: Tick) -> bool | None:
    """#172 AC2: `claude auth status` with the build environment; None when unreadable."""
    prefix = [f"{key}={value}" for key, value in claude_env(tick.settings).items()]
    command = ["claude", "auth", "status"]
    _, out = tick.host.run(["env", *prefix, *command] if prefix else command)
    try:
        data = json.loads(out)
    except ValueError:
        return None
    flag = data.get("loggedIn") if isinstance(data, dict) else None
    return flag if isinstance(flag, bool) else None


def sign_in_ok(tick: Tick) -> bool:
    """#172 AC2, AC3: signed out means no build and no label change; told once per sign-out."""
    marker = tick.home / "signed-out"
    state = signed_in(tick)
    if state is None:
        return True
    if state:
        marker.unlink(missing_ok=True)
        return True
    folder = tick.settings.claude_config_dir or "~/.claude"
    tick.say(f"{SIGNED_OUT_TEXT} ({folder}); no build started")
    if not marker.exists():
        marker.write_text(folder)
        tick.notify(
            f"ReviewRadar {SIGNED_OUT_TEXT} ({folder}); builds wait. "
            f"Sign in with: CLAUDE_CONFIG_DIR={folder} claude auth login"
        )
    return False


def take_lock(host: Host, lock: Path) -> bool:
    """A lock younger than 15 minutes means another tick runs; an older one is left over."""
    try:
        lock.mkdir(parents=True)
        return True
    except FileExistsError:
        if host.now() - lock.stat().st_mtime < LOCK_MAX_AGE:
            return False
    lock.rmdir()
    lock.mkdir()
    return True


def running_keys(tick: Tick) -> dict[str, bool]:
    """Key of each build whose wrapper is alive, and whether it runs alone."""
    found: dict[str, bool] = {}
    if not tick.runs.exists():
        return found
    for run in sorted(tick.runs.iterdir()):
        pid_file = run / "pid"
        if pid_file.exists() and tick.host.alive(int(pid_file.read_text().strip())):
            found[run.name] = (run / "alone").exists()
    return found


def log_tail(run: Path) -> str:
    log = run / "log.txt"
    lines = log.read_text(errors="replace").splitlines() if log.exists() else []
    return "\n".join(lines[-LOG_TAIL:])


def is_loop_pr(pr: dict[str, Any]) -> bool:
    """The marker, from this repository, and not opened by another login (#74 AC1)."""
    login = (pr.get("author") or {}).get("login")
    if pr.get("isCrossRepository") or (login and login != OWNER):
        return False
    return MARKER in (pr.get("body") or "")


def loop_pull_requests(tick: Tick) -> list[dict[str, Any]]:
    """All states with light fields, open ones with every field: GitHub caps a query at 500,000
    nodes, and the heavy fields cost about 10,000 per pull request asked for."""
    light = "number,state,body,labels,headRefName,author,isCrossRepository,createdAt"
    heavy = light + ",commits,comments,statusCheckRollup,isDraft,mergeStateStatus,headRefOid"
    heavy += ",baseRefName,title"
    every = tick.gh_json(
        "pr", "list", "--state", "all", "--limit", str(ALL_PR_LIMIT), "--json", light
    )
    opened = [
        pr
        for pr in tick.gh_json(
            "pr", "list", "--state", "open", "--limit", str(OPEN_PR_LIMIT), "--json", heavy
        )
        if pr.get("state") == "OPEN"
    ]
    seen = {pr["number"] for pr in opened}
    ended = [pr for pr in every if pr["number"] not in seen and pr.get("state") != "OPEN"]
    return [pr for pr in opened + ended if is_loop_pr(pr)]


def closes(pr: dict[str, Any]) -> int | None:
    match = re.search(r"Closes #(\d+)", pr.get("body") or "")
    return int(match.group(1)) if match else None


def names(item: dict[str, Any]) -> set[str]:
    return {label["name"] for label in item.get("labels") or []}


def report_link(pr: dict[str, Any]) -> str:
    match = re.search(r"https://claude\.ai/artifact/\S+", pr.get("body") or "")
    return match.group(0).rstrip(").,") if match else "no link in the pull request"


def status_label(pr: dict[str, Any]) -> str:
    found = sorted(names(pr) & PR_LABELS)
    return found[0] if found else "no status label yet"


def pr_message(pr: dict[str, Any], verb: str) -> str:
    """#68: one message with the pull request and report links, from the list already read."""
    number = pr["number"]
    return (
        f"ReviewRadar PR #{number} {verb} for #{closes(pr)} ({status_label(pr)})\n"
        f"https://github.com/{REPO}/pull/{number}\nReport: {report_link(pr)}"
    )


def newest_open_pr(prs: list[dict[str, Any]], issue: int) -> dict[str, Any] | None:
    found = [pr for pr in prs if pr["state"] == "OPEN" and closes(pr) == issue]
    return max(found, key=lambda pr: pr["number"]) if found else None


def finish_runs(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """AC10: handle every build that ended since the last tick, then archive its run folder."""
    if not tick.runs.exists():
        return
    for run in sorted(tick.runs.iterdir()):
        pid_file = run / "pid"
        if not run.is_dir() or not pid_file.exists():
            continue
        if tick.host.alive(int(pid_file.read_text().strip())):
            continue
        exit_file = run / "exit"
        outcome = exit_file.read_text().strip() if exit_file.exists() else "gone"
        handle_end(tick, run, outcome, prs)
        archive = tick.runs / "done" / f"{run.name}-{int(tick.host.now())}"
        archive.parent.mkdir(exist_ok=True)
        run.rename(archive)


def handle_end(tick: Tick, run: Path, outcome: str, prs: list[dict[str, Any]]) -> None:
    key = run.name
    kind, number = key.split("-", 1)
    worktree = tick.home / "worktrees" / key
    tail = log_tail(run)
    limit = outcome != "no-artifact" and USAGE_LIMIT.search(tail) is not None
    if outcome == "0" and kind == "pr":
        remove_worktree(tick, worktree)
        tick.say(f"{key}: ended normally")
        pr = next((p for p in prs if p["number"] == int(number)), None)
        if pr is not None and pr["state"] == "OPEN":
            tick.notify(pr_message(pr, "updated"))
        return
    reason = {
        "0": "ended without a pull request",
        "timeout": "stopped after 45 minutes",
        "gone": "stopped with no exit code",
        "no-artifact": f"started {STARTS} times without the Artifact tool",
    }.get(outcome, f"ended with error {outcome}")
    if kind == "pr" and limit:
        pause_for_limit(tick, key, number, worktree)
        return
    if kind == "pr":
        tick.say(f"{key}: {reason}; worktree kept")
        tick.notify(f"ReviewRadar build for pull request #{number} {reason}")
        return
    labels = names(tick.gh_json("issue", "view", number, "--json", "labels"))
    has_pr = any(closes(pr) == int(number) for pr in prs)
    opened = newest_open_pr(prs, int(number))
    if "agent:running" not in labels or has_pr:
        remove_worktree(tick, worktree)
        tick.say(
            f"{key}: ended normally"
            if outcome == "0"
            else f"{key}: {reason}, but the build already handed over"
        )
        if opened is not None:
            tick.notify(pr_message(opened, "opened"))
        elif not has_pr and "agent:failed" in labels:
            record_failure(tick, int(number), "stopped", "set agent:failed itself")
        return
    if limit:
        pause_for_limit(tick, key, number, worktree)
        return
    ensure_label(tick, "agent:failed")
    tick.gh(
        "issue",
        "edit",
        number,
        "--add-label",
        "agent:failed",
        "--remove-label",
        "agent:running,agent:ready",
    )
    body = f"{MARKER}\nThe loop build {reason}."
    if outcome == "no-artifact" and not (
        tick.settings.claude_entrypoint or os.environ.get("CLAUDE_CODE_ENTRYPOINT")
    ):
        body += " CLAUDE_CODE_ENTRYPOINT is not set in agent.env."
    body += f" Last {LOG_TAIL} lines of the log:\n"
    body += f"\n```\n{tail}\n```"
    tick.gh("issue", "comment", number, "--body", body)
    tick.say(f"{key}: {reason}; agent:failed, worktree kept")
    tick.notify(f"ReviewRadar build for issue #{number} failed: {reason}")
    record_failure(tick, int(number), "stopped" if outcome == "0" else "transient", reason)


def failed_record(tick: Tick, number: int) -> dict[str, Any] | None:
    path = tick.home / "failed" / str(number)
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_record(tick: Tick, number: int, record: dict[str, Any]) -> None:
    folder = tick.home / "failed"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / str(number)).write_text(json.dumps(record, sort_keys=True))


def main_head(tick: Tick) -> str:
    """The origin/main commit, fetched once per tick; empty when it cannot be read."""
    if tick.main_head is None:
        git = ["git", "-C", str(REPO_ROOT)]
        tick.host.run([*git, "fetch", "origin", "main"])
        code, out = tick.host.run([*git, "rev-parse", "origin/main"])
        head = out.strip() if code == 0 else ""
        tick.main_head = head if re.fullmatch(r"[0-9a-f]{7,40}", head) else ""
    return tick.main_head


def record_failure(tick: Tick, number: int, kind: str, outcome: str) -> None:
    """#149 AC1, AC4: what failed and on which main; retries are kept from the last record."""
    old = failed_record(tick, number) or {}
    retries = int(old.get("retries") or 0)
    record = {"main": main_head(tick), "kind": kind, "retries": retries, "outcome": outcome}
    stacked = stacked_record(tick, number)
    if stacked is not None and stacked.get("head"):
        record["parent"] = stacked["head"]
    if retries >= RETRIES:
        if not old.get("told"):
            tick.notify(
                f"ReviewRadar #{number} failed after {RETRIES} retries, needs you: "
                f"https://github.com/{REPO}/issues/{number}"
            )
        record["told"] = True
    write_record(tick, number, record)


def stacked_record(tick: Tick, number: int) -> dict[str, Any] | None:
    """#165 AC2: the parent pull request, branch and head commit a stacked build started on."""
    try:
        data = json.loads((tick.home / "stacked" / str(number)).read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def tidy_failed(tick: Tick) -> None:
    """#149 AC6: a record leaves when its issue is closed or restarted by hand."""
    folder = tick.home / "failed"
    if not folder.exists():
        return
    by_number = {item["number"]: item for item in open_issue_list(tick)}
    paused_marks = tick.home / "limit-paused"
    for path in sorted(folder.iterdir()):
        if not path.name.isdigit():
            continue
        number = int(path.name)
        item = by_number.get(number)
        labels = names(item) if item is not None else set()
        restarted = "agent:ready" in labels and "agent:failed" not in labels
        if item is not None and not restarted:
            continue
        if item is not None and (paused_marks / path.name).exists():
            continue
        archive = tick.home / "archive"
        archive.mkdir(exist_ok=True)
        path.rename(archive / f"failed-{number}-{int(tick.host.now())}")
        why = "closed" if item is None else "restarted by hand"
        tick.say(f"issue-{number}: {why}, failure record archived")


def retry_reason(tick: Tick, item: dict[str, Any], parent_pr: dict[str, Any] | None = None) -> str:
    """#149 AC2, #165 AC9: why a failed issue may start again, or empty when it may not."""
    number = item["number"]
    labels = names(item)
    if "agent:ready" in labels or labels & (SKIP_LABELS - {"agent:failed"}):
        return ""
    record = failed_record(tick, number)
    if record is None:
        record = {"main": main_head(tick), "kind": "stopped", "retries": 0, "outcome": ""}
        write_record(tick, number, record)
        tick.say(f"issue-{number}: failed with no record; recorded, waits for main to move")
        return ""
    if int(record.get("retries") or 0) >= RETRIES:
        return ""
    if record.get("kind") == "transient":
        return f"the last build {record.get('outcome') or 'failed'}"
    old, new = str(record.get("main") or ""), main_head(tick)
    if not old and new:
        write_record(tick, number, record | {"main": new})
        return ""
    if old and new and old != new:
        return f"main moved from {old[:7]} to {new[:7]}"
    was = str(record.get("parent") or "")
    now = str((parent_pr or {}).get("headRefOid") or "")
    if parent_pr is not None and was and now and was != now:
        return f"the parent pull request #{parent_pr['number']} moved from {was[:7]} to {now[:7]}"
    return ""


def pause_for_limit(tick: Tick, key: str, number: str, worktree: Path) -> None:
    """#74 AC5: a build stopped by the plan limit before its hand-over; any exit code."""
    if key.startswith("issue-"):
        tick.gh(
            "issue", "edit", number, "--add-label", "agent:ready", "--remove-label", "agent:running"
        )
        if failed_record(tick, int(number)) is not None:
            marks = tick.home / "limit-paused"
            marks.mkdir(exist_ok=True)
            (marks / number).touch()
    remove_worktree(tick, worktree)
    until = tick.host.now() + PAUSE_SECONDS
    (tick.home / "paused-until").write_text(str(int(until)))
    tick.say(f"{key}: plan limit reached, paused 60 minutes")
    tick.notify(f"ReviewRadar loop paused 60 minutes: plan limit reached ({key})")


def remove_worktree(tick: Tick, worktree: Path) -> None:
    if worktree.exists():
        tick.host.run(["git", "-C", str(REPO_ROOT), "worktree", "remove", str(worktree)])


def ensure_label(tick: Tick, label: str) -> None:
    existing = {
        item["name"] for item in tick.gh_json("label", "list", "--json", "name", "--limit", "200")
    }
    if label not in existing:
        color, description = LABEL_COLORS[label]
        tick.gh("label", "create", label, "--color", color, "--description", description)


def is_approval(body: str) -> bool:
    """#80 AC1: the whole comment is one of the approval words."""
    return body.strip().lower().rstrip(".!,:;").strip() in APPROVALS


def summary_mark(comment: dict[str, Any]) -> bool:
    """A rocket or confused in the reaction summary (gh's reactionGroups or REST reactions)."""
    for group in comment.get("reactionGroups") or []:
        if str(group.get("content", "")).lower() in DONE_MARKS and (
            (group.get("users") or {}).get("totalCount", 0) > 0
        ):
            return True
    reactions = comment.get("reactions") or {}
    return any(int(reactions.get(mark) or 0) > 0 for mark in DONE_MARKS)


def remark_of(kind: str, comment: dict[str, Any]) -> Remark | None:
    login = (comment.get("author") or comment.get("user") or {}).get("login")
    body = comment.get("body") or ""
    if login != OWNER or MARKER in body:
        return None
    number: int | None = comment["id"] if isinstance(comment.get("id"), int) else None
    match = COMMENT_ID.search(comment.get("url") or comment.get("html_url") or "")
    if number is None and match:
        number = int(match.group(1))
    created = comment.get("createdAt") or comment.get("created_at") or ""
    return Remark(kind, number, body, created, summary_mark(comment))


def remarks_of(tick: Tick, pr: dict[str, Any]) -> list[Remark]:
    """Owner comments of a loop pull request: conversation, line comments, /redo on its issue."""
    number = pr["number"]
    if number in tick.remarks:
        return tick.remarks[number]
    found = [r for c in pr.get("comments") or [] if (r := remark_of("conversation", c))]
    code, out = tick.host.run(["gh", "api", f"repos/{REPO}/pulls/{number}/comments", "--paginate"])
    try:
        inline = json.loads(out) if code == 0 else []
    except ValueError:
        inline = []
    if isinstance(inline, list):
        found += [r for c in inline if isinstance(c, dict) and (r := remark_of("inline", c))]
    issue = closes(pr)
    if issue is not None:
        comments = tick.gh_json("issue", "view", str(issue), "--json", "comments")["comments"]
        found += [r for c in comments if (r := remark_of("issue", c))]
    tick.remarks[number] = found
    return found


def done_by_owner(tick: Tick, remark: Remark) -> bool:
    """#80 AC6, AC7: a rocket or confused by the owner; reactions are read only when summed."""
    if remark.marked is None:
        remark.marked = False
        if remark.has_summary_mark and remark.id is not None:
            path = "pulls/comments" if remark.kind == "inline" else "issues/comments"
            code, out = tick.host.run(
                ["gh", "api", f"repos/{REPO}/{path}/{remark.id}/reactions", "--paginate"]
            )
            try:
                reactions = json.loads(out) if code == 0 else []
            except ValueError:
                reactions = []
            remark.marked = any(
                isinstance(r, dict)
                and (r.get("user") or {}).get("login") == OWNER
                and r.get("content") in DONE_MARKS
                for r in reactions
                if isinstance(reactions, list)
            )
    return remark.marked


def last_commit_date(pr: dict[str, Any], skip_updates: bool = False) -> str:
    commits = pr.get("commits") or []
    if skip_updates:
        commits = [
            c
            for c in commits
            if not str(c.get("messageHeadline") or "").startswith(UPDATE_FROM_MAIN)
        ]
    return str(commits[-1].get("committedDate", "")) if commits else ""


def open_requests(tick: Tick, pr: dict[str, Any]) -> list[Remark]:
    """#80 AC6: owner comments with no done mark, created after the pull request was opened.

    A comment without an id cannot carry a mark; it counts only as an owner /redo newer than
    the last commit, as before.
    """
    opened = pr.get("createdAt") or ""
    since = last_commit_date(pr)
    found = []
    for remark in remarks_of(tick, pr):
        if remark.created <= opened:
            continue
        if remark.kind == "conversation" and is_approval(remark.body):
            continue
        if remark.kind == "issue" and not remark.body.startswith("/redo"):
            continue
        if remark.id is None:
            if remark.body.startswith("/redo") and remark.created > since:
                found.append(remark)
            continue
        if not done_by_owner(tick, remark):
            found.append(remark)
    return sorted(found, key=lambda r: r.created)


def redo_count(tick: Tick, pr: dict[str, Any]) -> int:
    """#78 AC1: the open change requests of a pull request."""
    return len(open_requests(tick, pr))


def pr_needs_run(tick: Tick, pr: dict[str, Any]) -> bool:
    """AC4: the cases of work-queue section 1; an ended pull request is tidied, not run."""
    labels = names(pr)
    if pr["state"] != "OPEN":
        return False
    if open_requests(tick, pr):
        return True
    if "pr:blocked" in labels:
        return False
    if not labels & PR_LABELS:
        return True
    checks = pr.get("statusCheckRollup") or []
    red = any((c.get("conclusion") or c.get("state") or "") in RED_CI for c in checks)
    return "pr:ready-for-review" in labels and red


def labelled_by_owner(tick: Tick, number: int) -> bool:
    ready = '.[] | select(.event == "labeled" and .label.name == "agent:ready") | .actor.login'
    events = f"repos/{REPO}/issues/{number}/events"
    code, out = tick.host.run(["gh", "api", events, "--paginate", "--jq", ready])
    logins = out.split()
    return code == 0 and bool(logins) and logins[-1] == OWNER


def depends_on(body: str) -> set[int]:
    """Every #number on each line that starts with 'Depends on'."""
    found: set[int] = set()
    for rest in DEPENDS_LINE.findall(body):
        found |= {int(n) for n in re.findall(r"#(\d+)", rest)}
    return found


def files_of(body: str) -> set[str]:
    """The backticked paths of the bullet lines under '## Files likely touched'."""
    heading = FILES_HEADING.search(body)
    if heading is None:
        return set()
    section = body[heading.end() :]
    following = re.search(r"^##\s", section, re.MULTILINE)
    section = section[: following.start()] if following else section
    paths = set()
    for path in BULLET_PATH.findall(section):
        path = path.strip().removeprefix("./").removeprefix(LAB_PREFIX)
        if path:
            paths.add(path)
    return paths


def runs_alone(issue: dict[str, Any]) -> bool:
    """risk:high, a migration or model change, or no files listed (an empty body is not checked)."""
    body = issue.get("body") or ""
    no_files = bool(body.strip()) and not files_of(body)
    return "risk:high" in names(issue) or any(word in body for word in ALONE_WORDS) or no_files


def closed_as_not_planned(tick: Tick, number: int) -> bool:
    """#143 AC3: only an explicit NOT_PLANNED fails a dependency; unreadable counts as done."""
    if number not in tick.not_planned:
        code, out = tick.gh("issue", "view", str(number), "--json", "stateReason")
        reason = ""
        if code == 0:
            try:
                data = json.loads(out)
            except ValueError:
                data = {}
            if isinstance(data, dict):
                reason = str(data.get("stateReason") or "").upper().replace(" ", "_")
        tick.not_planned[number] = reason == "NOT_PLANNED"
    return tick.not_planned[number]


def unmet(tick: Tick, depends: set[int], open_numbers: set[int]) -> set[int]:
    """The dependencies that are still open or were closed as not planned."""
    return {m for m in depends if m in open_numbers or closed_as_not_planned(tick, m)}


def open_issue_list(tick: Tick) -> list[dict[str, Any]]:
    if tick.open_issues is None:
        tick.open_issues = tick.gh_json(
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "200",
            "--json",
            "number,title,body,labels,createdAt",
        )
    return tick.open_issues


def main_is_red(tick: Tick) -> bool:
    """#70 AC5: the latest completed Checks run on main; unreadable counts as green."""
    code, out = tick.gh(
        "run",
        "list",
        "--workflow",
        "checks.yml",
        "--branch",
        "main",
        "--status",
        "completed",
        "--limit",
        "1",
        "--json",
        "conclusion,headSha,url",
    )
    try:
        runs = json.loads(out) if code == 0 else None
    except ValueError:
        runs = None
    if not isinstance(runs, list) or not runs or not isinstance(runs[0], dict):
        tick.say("main checks could not be read; going on as if main were green")
        return False
    run = runs[0]
    if run.get("conclusion") == "success":
        return False
    sha = str(run.get("headSha") or "")[:7]
    last = tick.home / "last-red"
    if not (last.exists() and last.read_text() == sha):
        last.write_text(sha)
        tick.notify(f"main is red at {sha}: {run.get('url')}")
    tick.say(f"main is red at {sha}; no new issue starts")
    return True


def shared_holder(
    busy: dict[str, int], owners: dict[str, set[int]], path: str, ignored: set[int]
) -> int:
    """The issue that holds a path for this one, or 0; #165 AC3 ignores the parents' files."""
    first = busy.get(path, 0)
    if first not in ignored:
        return first
    others = sorted(owners.get(path, set()) - ignored)
    return others[0] if others else 0


def stack_parent(
    tick: Tick, prs: list[dict[str, Any]], parent: int, open_numbers: set[int]
) -> dict[str, Any] | None:
    """#165 AC1: the green, ready loop pull request of the one unmerged dependency, if any."""
    if parent not in open_numbers:
        return None
    found = newest_open_pr(prs, parent)
    if found is None or found.get("isDraft"):
        return None
    if not found.get("headRefName") or not found.get("headRefOid"):
        return None  # the record of AC2 needs the branch and its head commit
    checks = [check_state(c) for c in found.get("statusCheckRollup") or []]
    if "pr:ready-for-review" not in names(found) or not checks or set(checks) != {"green"}:
        return None
    return found


def stack_issues(prs: list[dict[str, Any]], parent_pr: dict[str, Any]) -> set[int]:
    """#165 AC3: the parent issue and the parents of its own pull request, down a chain."""
    ignored = {closes(parent_pr) or 0}
    current = parent_pr
    for _ in range(len(prs)):
        base = str(current.get("baseRefName") or "main")
        up = next((p for p in prs if p["state"] == "OPEN" and p.get("headRefName") == base), None)
        if base == "main" or up is None or (closes(up) or 0) in ignored:
            break
        ignored.add(closes(up) or 0)
        current = up
    return ignored - {0}


def choose(tick: Tick, prs: list[dict[str, Any]], running: dict[str, bool]) -> list[Target]:
    """AC3 to AC6: pull requests first, then the oldest ready issues, within the free slots."""
    free = tick.settings.concurrency - len(running)
    chosen: list[Target] = []
    if free <= 0:
        return chosen
    for pr in prs:
        key = f"pr-{pr['number']}"
        if len(chosen) < free and key not in running and pr_needs_run(tick, pr):
            prompt = f"Use the work-queue skill for pull request #{pr['number']} only."
            count = redo_count(tick, pr)
            what = f"{count} change requests open" if count else "CI"
            message = f"ReviewRadar working on PR #{pr['number']} ({what})"
            chosen.append(
                Target(key, pr["number"], prompt, branch=pr["headRefName"], message=message)
            )
    if any(running.values()) or tick.main_red:
        return chosen
    issues = open_issue_list(tick)
    busy: dict[str, int] = {}
    owners: dict[str, set[int]] = {}
    for item in issues:
        if names(item) & {"agent:running", "agent:review"}:
            for path in files_of(item.get("body") or ""):
                busy.setdefault(path, item["number"])
                owners.setdefault(path, set()).add(item["number"])
    open_numbers = {item["number"] for item in issues}
    ready = sorted(
        (i for i in issues if "agent:ready" in names(i)),
        key=lambda i: (i["createdAt"], i["number"]),
    )
    failed = sorted(
        (i for i in issues if "agent:failed" in names(i)),
        key=lambda i: (i["createdAt"], i["number"]),
    )
    for issue in [*ready, *failed]:
        if len(chosen) >= free:
            break
        key = f"issue-{issue['number']}"
        depends = depends_on(issue.get("body") or "")
        retry = ""
        waiting = unmet(tick, depends, open_numbers)
        parent_pr = (
            stack_parent(tick, prs, next(iter(waiting)), open_numbers)
            if len(waiting) == 1
            else None
        )
        held = bool(waiting) and parent_pr is None
        if "agent:failed" in names(issue) and "agent:ready" not in names(issue):
            if key in running or held:
                continue
            retry = retry_reason(tick, issue, parent_pr)
            if not retry:
                continue
        elif key in running or names(issue) & SKIP_LABELS or held:
            continue
        files = files_of(issue.get("body") or "")
        ignored = stack_issues(prs, parent_pr) if parent_pr is not None else set()
        shared = [p for p in sorted(files) if shared_holder(busy, owners, p, ignored)]
        if shared:
            holder = shared_holder(busy, owners, shared[0], ignored)
            tick.say(f"{key}: waits for #{holder}, which also touches {shared[0]}")
            continue
        if not labelled_by_owner(tick, issue["number"]):
            tick.say(f"{key}: agent:ready was not added by {OWNER}; skipped")
            continue
        prompt = f"Use the work-queue skill for issue #{issue['number']} only."
        title = issue.get("title") or ""
        message = f"ReviewRadar started #{issue['number']}: {title}" if title else ""
        stack: dict[str, Any] = {}
        if parent_pr is not None:
            branch = str(parent_pr["headRefName"])
            prompt += (
                f" Stacked on pull request #{parent_pr['number']}: branch from origin/{branch}"
                f" and open the pull request into {branch}."
            )
            head_title = parent_pr.get("title") or title
            message = (
                f"ReviewRadar started #{issue['number']} on top of PR "
                f"#{parent_pr['number']}: {head_title}"
            )
            stack = {
                "stack_pr": parent_pr["number"],
                "stack_branch": branch,
                "stack_head": str(parent_pr.get("headRefOid") or ""),
            }
        if retry:
            record = failed_record(tick, issue["number"]) or {}
            count = int(record.get("retries") or 0) + 1
            message = f"ReviewRadar retrying #{issue['number']} ({count} of {RETRIES})"
        if runs_alone(issue):
            if running or chosen:
                break
            chosen.append(
                Target(
                    key, issue["number"], prompt, alone=True, message=message, retry=retry, **stack
                )
            )
            break
        chosen.append(Target(key, issue["number"], prompt, message=message, retry=retry, **stack))
        for path in files:
            busy.setdefault(path, issue["number"])
            owners.setdefault(path, set()).add(issue["number"])
    return chosen


def start(tick: Tick, target: Target) -> bool:
    """AC7 to AC9: worktree, uv sync, claim, then the build in the background."""
    worktree = tick.home / "worktrees" / target.key
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git = ["git", "-C", str(REPO_ROOT)]
    if worktree.exists():
        aside = worktree.with_name(f"{target.key}-{int(tick.host.now())}")
        tick.host.run([*git, "worktree", "move", str(worktree), str(aside)])
        archive_branches(tick, target, aside)
    elif target.retry:
        archive_branches(tick, target, None)
    wanted = [b for b in (target.branch, target.stack_branch) if b]
    tick.host.run([*git, "fetch", "origin", "main", *wanted])
    if target.stack_branch:
        add = [*git, "worktree", "add", "--detach", str(worktree), f"origin/{target.stack_branch}"]
    elif target.branch:
        add = [
            *git,
            "worktree",
            "add",
            "-B",
            target.branch,
            str(worktree),
            f"origin/{target.branch}",
        ]
    else:
        add = [*git, "worktree", "add", "--detach", str(worktree), "origin/main"]
    lab = worktree / "claude-code-training-lab"
    for step, cwd in ((add, None), (["uv", "sync", "--frozen"], lab)):
        code, out = tick.host.run(step, cwd=cwd)
        if code != 0:
            name = " ".join(step[:4]) if step[0] != "git" else " ".join(step[3:5])
            tick.say(f"{target.key}: not started, {' '.join(step[:4])} failed: {out.strip()}")
            start_failed(tick, target, name)
            return False
    (tick.home / "start-failed" / target.key).unlink(missing_ok=True)
    if target.key.startswith("issue-"):
        stacked = tick.home / "stacked" / str(target.number)
        if target.stack_branch:
            stacked.parent.mkdir(parents=True, exist_ok=True)
            info = {"pr": target.stack_pr, "branch": target.stack_branch, "head": target.stack_head}
            stacked.write_text(json.dumps(info, sort_keys=True))
        else:
            stacked.unlink(missing_ok=True)
        ensure_label(tick, "agent:running")
        remove = "agent:ready,agent:failed" if target.retry else "agent:ready"
        tick.gh(
            "issue",
            "edit",
            str(target.number),
            "--add-label",
            "agent:running",
            "--remove-label",
            remove,
        )
        (tick.home / "limit-paused" / str(target.number)).unlink(missing_ok=True)
    if target.retry:
        record = failed_record(tick, target.number) or {}
        count = int(record.get("retries") or 0) + 1
        kept = {k: v for k, v in record.items() if k != "parent"}
        parent = {"parent": target.stack_head} if target.stack_head else {}
        write_record(tick, target.number, kept | {"retries": count} | parent)
        tick.gh(
            "issue",
            "comment",
            str(target.number),
            "--body",
            f"{MARKER}\nRetry {count} of {RETRIES}: {target.retry}.",
        )
        tick.say(f"{target.key}: retry {count} of {RETRIES}: {target.retry}")
    run = tick.runs / target.key
    run.mkdir(parents=True, exist_ok=True)
    if target.alone:
        (run / "alone").touch()
    wrapper = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        str(run),
        str(lab),
        target.prompt,
    ]
    pid = tick.host.spawn(wrapper, run / "log.txt")
    (run / "pid").write_text(str(pid))
    tick.say(f"{target.key}: started (pid {pid})")
    if target.message:
        tick.notify(target.message)
    return True


def archive_branches(tick: Tick, target: Target, aside: Path | None) -> None:
    """#74 AC7: free the branches of a kept worktree; rename to archive/, delete nothing."""
    git = ["git", "-C", str(REPO_ROOT)]
    stamp = int(tick.host.now())
    found: list[str] = []
    if aside is not None:
        code, out = tick.host.run(["git", "-C", str(aside), "branch", "--show-current"])
        if code == 0 and out.strip():
            found.append(out.strip())
    if target.key.startswith("issue-"):
        patterns = [f"{kind}/{target.number}-*" for kind in ("bug", "feat", "task")]
        code, out = tick.host.run(
            [*git, "branch", "--list", *patterns, "--format=%(refname:short)"]
        )
        if code == 0:
            found += [line.strip() for line in out.splitlines() if line.strip()]
    for branch in dict.fromkeys(found):
        if branch.startswith("archive/"):
            continue
        tick.host.run([*git, "branch", "-m", branch, f"archive/{branch}-{stamp}"])
        tick.say(f"{target.key}: branch {branch} renamed to archive/{branch}-{stamp}")


def start_failed(tick: Tick, target: Target, step: str) -> None:
    """#74 AC8: one ntfy per key and step until that key starts once."""
    folder = tick.home / "start-failed"
    folder.mkdir(exist_ok=True)
    mark = folder / target.key
    if mark.exists() and mark.read_text() == step:
        return
    mark.write_text(step)
    what = (
        f"issue #{target.number}"
        if target.key.startswith("issue-")
        else (f"pull request #{target.number}")
    )
    tick.notify(f"ReviewRadar build for {what} did not start: {step} failed")


def pull_main(tick: Tick) -> None:
    """#74 AC2, AC3: fast-forward the main checkout when it is on main with no tracked change."""
    git = ["git", "-C", str(REPO_ROOT)]
    code, branch = tick.host.run([*git, "branch", "--show-current"])
    branch = branch.strip()
    if code != 0 or not branch:
        tick.say("main checkout: the branch could not be read; not updated")
        tick.pull_problem = "the branch could not be read"
        return
    reason = ""
    if branch != "main":
        reason = f"the checkout is on {branch}"
    else:
        code, changes = tick.host.run([*git, "status", "--porcelain", "--untracked-files=no"])
        if code != 0 or changes.strip():
            reason = "it has tracked changes"
        elif tick.host.run([*git, "fetch", "origin", "main"])[0] != 0:
            reason = "git fetch failed"
        elif tick.host.run([*git, "merge", "--ff-only", "origin/main"])[0] != 0:
            reason = "the fast-forward failed"
    tick.pull_problem = reason
    last = tick.home / "last-pull-problem"
    if not reason:
        last.unlink(missing_ok=True)
        (tick.home / "last-pull-problem-sent").unlink(missing_ok=True)
        tick.say("main checkout: pulled")
        return
    tick.say(f"main checkout not updated: {reason}")
    sent = tick.home / "last-pull-problem-sent"
    if last.exists() and last.read_text() == reason and not reminder_due(tick, sent):
        return
    last.write_text(reason)
    sent.write_text(str(tick.host.now()))
    tick.notify(f"ReviewRadar main checkout not updated: {reason}")


def reminder_due(tick: Tick, sent: Path) -> bool:
    """#167 AC4: the same pull problem is sent again 6 hours after it was last sent."""
    try:
        return tick.host.now() - float(sent.read_text()) >= REMINDER_SECONDS
    except (OSError, ValueError):
        return True


def tidy_ready(tick: Tick) -> set[int]:
    """#74 AC6: an issue handed over (agent:review) loses agent:ready; agent:failed keeps it."""
    fixed: set[int] = set()
    found = tick.gh_json(
        "issue",
        "list",
        "--state",
        "open",
        "--label",
        "agent:review",
        "--limit",
        "200",
        "--json",
        "number,labels",
    )
    for item in found:
        if "agent:ready" in names(item):
            tick.gh("issue", "edit", str(item["number"]), "--remove-label", "agent:ready")
            tick.say(f"issue-{item['number']}: handed over, agent:ready removed")
            fixed.add(item["number"])
    return fixed


def sync_review(tick: Tick, prs: list[dict[str, Any]], fixed: set[int]) -> None:
    """#146 AC2: an open issue with an open loop pull request is agent:review alone."""
    by_number = {item["number"]: item for item in open_issue_list(tick)}
    for pr in prs:
        number = closes(pr)
        item = by_number.get(number) if number is not None and pr["state"] == "OPEN" else None
        if number is None or item is None:
            continue
        have = names(item) - ({"agent:ready"} if number in fixed else set())
        stale = [x for x in ("agent:running", "agent:ready") if x in have]
        if "agent:review" in have and not stale:
            continue
        args = ["--add-label", "agent:review"] if "agent:review" not in have else []
        if stale:
            args += ["--remove-label", ",".join(stale)]
        tick.gh("issue", "edit", str(number), *args)
        item["labels"] = [{"name": x} for x in sorted((have | {"agent:review"}) - set(stale))]
        tick.say(f"issue-{number}: has PR #{pr['number']}, agent:review")


def tidy_ended(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """#143 AC1, AC7: labels of ended pull requests, and agent:ready of closed issues."""
    review: set[int] | None = None
    for pr in prs:
        if pr["state"] == "OPEN":
            continue
        stale = sorted(names(pr) & PR_LABELS)
        number = closes(pr)
        in_review = False
        if number is not None:
            if review is None:
                found = tick.gh_json(
                    "issue",
                    "list",
                    "--state",
                    "all",
                    "--label",
                    "agent:review",
                    "--limit",
                    "200",
                    "--json",
                    "number",
                )
                review = {item["number"] for item in found}
            in_review = number in review
        if not stale and not in_review:
            continue
        if stale:
            tick.gh("pr", "edit", str(pr["number"]), "--remove-label", ",".join(stale))
            pr["labels"] = [x for x in pr.get("labels") or [] if x["name"] not in PR_LABELS]
        if in_review and number is not None and review is not None:
            tick.gh("issue", "edit", str(number), "--remove-label", "agent:review")
            review.discard(number)
        tick.say(f"pr-{pr['number']}: tidied, labels removed")
    closed = tick.gh_json(
        "issue",
        "list",
        "--state",
        "closed",
        "--label",
        "agent:ready",
        "--limit",
        "200",
        "--json",
        "number,labels,state",
    )
    for item in closed:
        if item.get("state") == "CLOSED" and "agent:ready" in names(item):
            tick.gh("issue", "edit", str(item["number"]), "--remove-label", "agent:ready")
            tick.say(f"issue-{item['number']}: closed, agent:ready removed")


def paused(tick: Tick) -> bool:
    flag = tick.home / "paused-until"
    return flag.exists() and float(flag.read_text().strip() or 0) > tick.host.now()


def needs_you_head(pr: dict[str, Any]) -> str:
    commits = pr.get("commits") or []
    return (commits[-1].get("oid") or commits[-1].get("committedDate", "")) if commits else ""


def needs_you(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """#78 AC2: pr:blocked or pr:ci-failed, once per pull request, label and head commit."""
    seen_file = tick.home / "needs-you"
    seen = set(seen_file.read_text().split()) if seen_file.exists() else set()
    for pr in prs:
        if pr["state"] != "OPEN":
            continue
        head = needs_you_head(pr)
        for label in NEEDS_YOU:
            key = f"{pr['number']}:{label}:{head}"
            if label in names(pr) and key not in seen:
                seen.add(key)
                tick.notify(
                    f"ReviewRadar PR #{pr['number']} needs you: {label}\n"
                    f"https://github.com/{REPO}/pull/{pr['number']}"
                )
    seen_file.write_text("\n".join(sorted(seen)))


def announce_one(tick: Tick, pr: dict[str, Any]) -> None:
    head = f"ReviewRadar PR #{pr['number']} merged (#{closes(pr)})"
    if tick.pull_problem:
        tick.notify(f"{head}; main checkout not updated: {tick.pull_problem}")
    else:
        code, sha = tick.host.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"])
        tick.notify(f"{head}; main is now {sha.strip() if code == 0 else 'unknown'}")
    tick.say(f"pr-{pr['number']}: merged, announced")


def announce_merged(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """#78 AC4: each merged loop pull request once, after the pull of main of this tick."""
    record = tick.home / "announced-merged"
    merged = [pr for pr in prs if pr["state"] == "MERGED"]
    if not record.exists():
        record.write_text("\n".join(str(pr["number"]) for pr in merged))
        return
    done = set(record.read_text().split())
    for pr in merged:
        if str(pr["number"]) not in done:
            done.add(str(pr["number"]))
            announce_one(tick, pr)
    record.write_text("\n".join(sorted(done)))


def check_state(check: dict[str, Any]) -> str:
    """'green', 'running' or 'red' for one entry of statusCheckRollup."""
    status = str(check.get("status") or "").upper()
    conclusion = str(check.get("conclusion") or "").upper()
    state = str(check.get("state") or "").upper()
    if status and status != "COMPLETED":
        return "running"
    if conclusion:
        return "green" if conclusion in GREEN_CHECKS else "red"
    if state:
        return (
            "green"
            if state == "SUCCESS"
            else "running"
            if state in ("PENDING", "EXPECTED")
            else "red"
        )
    return "running"


def newest_approval(tick: Tick, pr: dict[str, Any]) -> Remark | None:
    """#80 AC1, AC5: the newest owner approval on the conversation without a done mark."""
    opened = pr.get("createdAt") or ""
    found = [
        r
        for r in remarks_of(tick, pr)
        if r.kind == "conversation"
        and r.id is not None
        and is_approval(r.body)
        and r.created > opened
        and not done_by_owner(tick, r)
    ]
    return max(found, key=lambda r: r.created) if found else None


def react(tick: Tick, remark: Remark, content: str) -> None:
    tick.host.run(
        [
            "gh",
            "api",
            "-X",
            "POST",
            f"repos/{REPO}/issues/comments/{remark.id}/reactions",
            "-f",
            f"content={content}",
        ]
    )
    remark.marked = True


def refuse_merge(tick: Tick, pr: dict[str, Any], approval: Remark, reason: str) -> None:
    """#80 AC4, AC5: no merge, 😕 on the approval, one message per pull request and reason."""
    number = pr["number"]
    react(tick, approval, "confused")
    tick.say(f"pr-{number}: not merged, {reason}")
    record = tick.home / "not-merged"
    seen = set(record.read_text().splitlines()) if record.exists() else set()
    key = f"{number}:{reason}"
    if key not in seen:
        seen.add(key)
        record.write_text("\n".join(sorted(seen)))
        tick.notify(f"ReviewRadar PR #{number} not merged: {reason}")


def parent_of(prs: list[dict[str, Any]], pr: dict[str, Any]) -> dict[str, Any] | None:
    """#165: the loop pull request whose branch is the base of this one, if the list has it."""
    base = pr.get("baseRefName")
    return next((p for p in prs if base and p.get("headRefName") == base and p is not pr), None)


def wait_for_parent(
    tick: Tick, prs: list[dict[str, Any]], pr: dict[str, Any], approval: Remark, base: str
) -> None:
    """#165 AC5: no merge into a branch that is not main; the approval stays valid, no reaction."""
    number = pr["number"]
    parent = parent_of(prs, pr)
    what = f"parent PR #{parent['number']}" if parent is not None else f"parent branch {base}"
    tick.say(f"pr-{number}: approved, not merged: it waits for its {what}")
    record = tick.home / "stack-waiting"
    seen = set(record.read_text().split()) if record.exists() else set()
    key = f"{number}:{approval.id}"
    if key not in seen:
        record.write_text("\n".join(sorted(seen | {key})))
        tick.notify(f"ReviewRadar PR #{number} not merged: it waits for its {what}")


def stacked_children(prs: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """#165: (child, parent) for each open loop pull request based on another one's branch."""
    found = []
    for child in prs:
        if child["state"] != "OPEN" or str(child.get("baseRefName") or "main") == "main":
            continue
        parent = parent_of(prs, child)
        if parent is not None and parent["state"] != "OPEN":
            found.append((child, parent))
    return found


def settle_children(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """#165 AC6, AC7: children of a merged parent go to main; of a closed one, pr:blocked."""
    record = tick.home / "parent-closed"
    seen = set(record.read_text().split()) if record.exists() else set()
    for child, parent in stacked_children(prs):
        number, up = child["number"], parent["number"]
        if parent["state"] == "MERGED":
            if number in tick.retargeted:
                continue
            code, out = tick.gh("pr", "edit", str(number), "--base", "main")
            if code != 0:
                tick.say(f"pr-{number}: base not changed to main ({out.strip()}); next tick")
                continue
            # Its checks and merge state were read against the old base: no merge this tick.
            tick.retargeted.add(number)
            tick.say(f"pr-{number}: parent PR #{up} merged; base is now main")
            continue
        key = f"{number}:{up}"
        if key in seen:
            continue
        other = ",".join(sorted(names(child) & PR_LABELS - {"pr:blocked"}))
        ensure_label(tick, "pr:blocked")
        edit = ["pr", "edit", str(number), "--add-label", "pr:blocked"]
        body = (
            f"{MARKER}\nThe parent pull request #{up} was closed without merge. "
            "This pull request is built on it and is not merged."
        )
        done = [
            tick.gh(*edit, *(["--remove-label", other] if other else []))[0],
            tick.gh("pr", "comment", str(number), "--body", body)[0],
        ]
        if any(done):
            tick.say(f"pr-{number}: parent PR #{up} closed; pr:blocked not complete, next tick")
            continue
        seen.add(key)
        record.write_text("\n".join(sorted(seen)))
        child["labels"] = [{"name": "pr:blocked"}]
        mine = tick.home / "needs-you"
        have = mine.read_text().split() if mine.exists() else []
        mine.write_text("\n".join(sorted({*have, f"{number}:pr:blocked:{needs_you_head(child)}"})))
        tick.say(f"pr-{number}: parent PR #{up} closed without merge; pr:blocked")
        tick.notify(f"ReviewRadar PR #{number} blocked: its parent PR #{up} was closed")


def merge_approved(tick: Tick, prs: list[dict[str, Any]], running: dict[str, bool]) -> None:
    """#80 AC2 to AC5: merge an open loop pull request on the owner's approval comment."""
    for pr in prs:
        number = pr["number"]
        if pr["state"] != "OPEN" or number in tick.retargeted:
            continue
        approval = newest_approval(tick, pr)
        if approval is None or approval.created <= last_commit_date(pr, skip_updates=True):
            continue
        base = str(pr.get("baseRefName") or "main")
        if base != "main":
            wait_for_parent(tick, prs, pr, approval, base)
            continue
        checks = [check_state(c) for c in pr.get("statusCheckRollup") or []]
        if pr.get("isDraft") or "pr:ready-for-review" not in names(pr) or not checks:
            tick.say(f"pr-{number}: approved, waiting for pr:ready-for-review and checks")
            continue
        if "running" in checks or open_requests(tick, pr) or f"pr-{number}" in running:
            tick.say(f"pr-{number}: approved, waiting for CI, change requests or a run")
            continue
        if "red" in checks:
            refuse_merge(tick, pr, approval, "a check is red")
            continue
        status = str(pr.get("mergeStateStatus") or "")
        if status == "BEHIND":
            code, out = tick.gh("pr", "update-branch", str(number))
            if code == 0:
                tick.say(f"pr-{number}: approved but behind main; branch updated")
            elif "conflict" in out.lower():
                tick.gh("pr", "comment", str(number), "--body", REDO_CONFLICT)
                refuse_merge(tick, pr, approval, "conflict with main; /redo posted")
            else:
                refuse_merge(tick, pr, approval, "the update from main failed")
            continue
        if status in ("DIRTY", "BLOCKED"):
            refuse_merge(tick, pr, approval, f"merge state is {status}")
            continue
        code, out = tick.gh(
            "pr",
            "merge",
            str(number),
            "--merge",
            "--delete-branch",
            "--match-head-commit",
            str(pr.get("headRefOid") or ""),
        )
        if code != 0:
            first = (out.strip().splitlines() or ["no output"])[0]
            refuse_merge(tick, pr, approval, f"the merge failed: {first}")
            continue
        react(tick, approval, "rocket")
        pr["state"] = "MERGED"
        tick.say(f"pr-{number}: merged on the owner's approval")
        pull_main(tick)
        record = tick.home / "announced-merged"
        done = set(record.read_text().split()) if record.exists() else set()
        record.write_text("\n".join(sorted(done | {str(number)})))
        announce_one(tick, pr)


def dependency_reason(
    tick: Tick, prs: list[dict[str, Any]], issues: dict[int, dict[str, Any]], number: int
) -> str:
    """#143 AC4: why a dependency has not unlocked its issue."""
    if number not in issues:
        return "closed as not planned, remove the dependency or reopen it"
    opened = newest_open_pr(prs, number)
    if opened is not None:
        return f"review PR #{opened['number']}"
    if "agent:running" in names(issues[number]):
        return "building"
    return "no pull request yet"


def blocked_lines(
    tick: Tick, prs: list[dict[str, Any]], running: dict[str, bool], started: set[str]
) -> tuple[int, list[str]]:
    """#143 AC4: the ready issues held back by a dependency or a shared file, one line each."""
    issues = open_issue_list(tick)
    by_number = {item["number"]: item for item in issues}
    busy: dict[str, int] = {}
    owners: dict[str, set[int]] = {}
    for item in issues:
        if names(item) & {"agent:running", "agent:review"}:
            for path in files_of(item.get("body") or ""):
                busy.setdefault(path, item["number"])
                owners.setdefault(path, set()).add(item["number"])
    ready = sorted(
        (i for i in issues if "agent:ready" in names(i) and not names(i) & SKIP_LABELS),
        key=lambda i: (i["createdAt"], i["number"]),
    )
    entries: list[tuple[int, int, str]] = []
    blocked: set[int] = set()
    for item in ready:
        number = item["number"]
        key = f"issue-{number}"
        body = item.get("body") or ""
        if key in running:
            continue
        waiting = unmet(tick, depends_on(body), set(by_number))
        parent_pr = (
            stack_parent(tick, prs, next(iter(waiting)), set(by_number))
            if len(waiting) == 1
            else None
        )
        found: list[tuple[int, str]] = [
            (m, f"#{number} waits for #{m}: {dependency_reason(tick, prs, by_number, m)}")
            for m in sorted(waiting)
            if parent_pr is None
        ]
        if not found:
            ignored = stack_issues(prs, parent_pr) if parent_pr is not None else set()
            shared: dict[int, str] = {}
            for path in sorted(files_of(body)):
                holder = shared_holder(busy, owners, path, ignored)
                if holder:
                    shared.setdefault(holder, path)
            found = [
                (m, f"#{number} waits for #{m}, which also touches {path}")
                for m, path in sorted(shared.items())
            ]
        if found and labelled_by_owner(tick, number):
            blocked.add(number)
            entries += [(number, m, text) for m, text in found]
        elif not found and key in started:
            for path in files_of(body):
                busy.setdefault(path, number)
    return len(blocked), [text for _, _, text in sorted(entries)]


def say_blocked(
    tick: Tick, prs: list[dict[str, Any]], running: dict[str, bool], started: set[str]
) -> None:
    """#143 AC4, AC5, AC6, AC8: one message when the blocked set changes."""
    count, lines = blocked_lines(tick, prs, running, started)
    last = tick.home / "last-blocked"
    if not lines:
        last.unlink(missing_ok=True)
        return
    for line in lines:
        tick.say(line)
    message = "\n".join([f"ReviewRadar waiting: {count} ready issues blocked", *lines])
    if last.exists() and last.read_text() == message:
        return
    last.write_text(message)
    tick.notify(message)


def queue_empty(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """AC12: 'queue empty' when no ready issue is left; blocked ones get #143's message."""
    waiting = sum(1 for pr in prs if pr["state"] == "OPEN")
    issues = tick.open_issues
    if issues is None:
        issues = tick.gh_json(
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "200",
            "--json",
            "number,title,body,labels,createdAt",
        )
    ready = [i for i in issues if "agent:ready" in names(i) and not names(i) & SKIP_LABELS]
    if ready:
        return
    message = f"ReviewRadar queue empty, {waiting} pull requests waiting"
    last = tick.home / "last-empty"
    if last.exists() and last.read_text() == message:
        return
    last.write_text(message)
    tick.say(message)
    tick.notify(message)


def tick_once(host: Host, home: Path) -> list[str]:
    """One tick; returns what it did, line by line."""
    settings = read_settings(home / "agent.env")
    tick = Tick(host, home, settings)
    lock = home / "tick.lock"
    if not take_lock(host, lock):
        tick.say("another tick is running; nothing done")
        return tick.log
    try:
        pull_main(tick)
        prs = loop_pull_requests(tick)
        sync_review(tick, prs, tidy_ready(tick))
        announce_merged(tick, prs)
        finish_runs(tick, prs)
        tidy_failed(tick)
        needs_you(tick, prs)
        running = running_keys(tick)
        settle_children(tick, prs)
        merge_approved(tick, prs, running)
        settle_children(tick, prs)
        tidy_ended(tick, prs)
        tick.main_red = main_is_red(tick)
        if paused(tick):
            tick.say("paused after the plan limit; no build started")
            return tick.log
        if not sign_in_ok(tick):
            return tick.log
        started = [t for t in choose(tick, prs, running) if start(tick, t)]
        say_blocked(tick, prs, running, {t.key for t in started})
        if started:
            (home / "last-empty").unlink(missing_ok=True)
        elif not running:
            queue_empty(tick, prs)
    finally:
        lock.rmdir()
    return tick.log


def run_build(
    run: Path, folder: Path, prompt: str, extra_env: Mapping[str, str] | None = None
) -> str:
    """The background wrapper: up to 3 starts of `claude -p`, 45 minutes in all; writes `exit`."""
    deadline = time.monotonic() + RUN_LIMIT
    outcome = "no-artifact"
    for number in range(1, STARTS + 1):
        if number > 1 and time.monotonic() >= deadline:
            outcome = "timeout"
            break
        outcome = run_start(run, folder, prompt, number, deadline, extra_env)
        if outcome != "no-artifact":
            break
    (run / "exit").write_text(outcome)
    return outcome


def stop_group(child: subprocess.Popen[str]) -> None:
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)


def read_lines(child: subprocess.Popen[str], lines: queue.Queue[str | None]) -> None:
    assert child.stdout is not None
    for line in child.stdout:
        lines.put(line)
    lines.put(None)


def with_newline(line: str) -> str:
    return line if line.endswith("\n") else line + "\n"


def run_start(
    run: Path,
    folder: Path,
    prompt: str,
    number: int,
    deadline: float,
    extra_env: Mapping[str, str] | None = None,
) -> str:
    """One `claude -p`; its output is the session log, a missing Artifact tool stops it."""
    env = {**os.environ, **(extra_env or {}), "REVIEWRADAR_LOOP": "1"}
    args = [
        "claude",
        "-p",
        prompt,
        "--max-turns",
        str(MAX_TURNS),
        "--output-format",
        "stream-json",
        "--verbose",
        "--allowedTools",
        "Artifact",
        "--append-system-prompt",
        HINT,
    ]
    with (run / "log.txt").open("a") as log, (run / f"session-{number}.jsonl").open("a") as session:
        log.write(f"start {number} of {STARTS}\n")
        log.flush()
        child = subprocess.Popen(
            args,
            cwd=folder,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=log,
            text=True,
            start_new_session=True,
        )
        lines: queue.Queue[str | None] = queue.Queue()
        threading.Thread(target=read_lines, args=(child, lines), daemon=True).start()
        seen_init = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                stop_group(child)
                return "timeout"
            try:
                line = lines.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                break
            session.write(with_newline(line))
            session.flush()
            try:
                event = json.loads(line)
            except ValueError:
                log.write(with_newline(line))
                log.flush()
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "system" and event.get("subtype") == "init" and not seen_init:
                seen_init = True
                if "Artifact" not in (event.get("tools") or []):
                    log.write(f"start {number}: no Artifact tool, stopped\n")
                    log.flush()
                    stop_group(child)
                    return "no-artifact"
            elif event.get("type") == "result" and isinstance(event.get("result"), str):
                log.write(with_newline(event["result"]))
                log.flush()
        try:
            return str(child.wait(timeout=max(deadline - time.monotonic(), 0)))
        except subprocess.TimeoutExpired:
            stop_group(child)
            return "timeout"


def announce_started(host: Host, home: Path, name: str) -> int:
    """#167 AC5: one 'loop started' message; no lock, no tick."""
    tick = Tick(host, home, read_settings(home / "agent.env"))
    tick.notify(f"ReviewRadar loop started on {name}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["run"] and len(argv) == 4:
        where = Path(os.environ.get("REVIEWRADAR_HOME", Path.home() / ".reviewradar"))
        settings = read_settings(where / "agent.env")
        run_build(Path(argv[1]), Path(argv[2]), argv[3], claude_env(settings))
        return 0
    home = Path(os.environ.get("REVIEWRADAR_HOME", Path.home() / ".reviewradar"))
    home.mkdir(parents=True, exist_ok=True)
    if argv[:1] == ["started"]:
        return announce_started(RealHost(), home, socket.gethostname())
    tick_once(RealHost(), home)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
