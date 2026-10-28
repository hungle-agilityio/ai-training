"""One tick of the loop: tidy ended builds, then start up to AGENT_CONCURRENCY new ones.

Run by `ops/start-loop.sh` every 10 minutes. Spec: specs/loop-concurrency/spec.md (AC1 to AC12).
`python ops/agent_tick.py` runs one tick; `python ops/agent_tick.py run <key> <folder> <prompt>`
is the background wrapper of one build (started by the tick, not by hand).
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import urllib.request
from collections.abc import Sequence
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
WAITING_CAP = 3
LOG_TAIL = 20
SKIP_LABELS = {"agent:running", "agent:review", "agent:failed", "agent:manual"}
PR_LABELS = {"pr:ready-for-review", "pr:changes-requested", "pr:blocked", "pr:ci-failed"}
RED_CI = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}
ALONE_WORDS = ("migrations/", "models.py")
USAGE_LIMIT = re.compile(r"usage limit|limit reached|rate_limit", re.IGNORECASE)
LABEL_COLORS = {
    "agent:running": ("FBCA04", "The loop is building this issue"),
    "agent:failed": ("D93F0B", "The loop could not finish this issue; see the comment"),
}
REPO_ROOT = Path(__file__).resolve().parents[2]


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
        request = urllib.request.Request(f"https://ntfy.sh/{topic}", data=message.encode())
        try:
            urllib.request.urlopen(request, timeout=10).close()
        except OSError as error:
            print(f"ntfy failed: {error}")


@dataclass(frozen=True)
class Settings:
    concurrency: int
    ntfy_topic: str


@dataclass(frozen=True)
class Target:
    key: str
    number: int
    prompt: str
    branch: str = ""
    alone: bool = False


@dataclass
class Tick:
    host: Host
    home: Path
    settings: Settings
    log: list[str] = field(default_factory=list)

    @property
    def runs(self) -> Path:
        return self.home / "runs"

    def say(self, line: str) -> None:
        self.log.append(line)
        print(line)

    def notify(self, message: str) -> None:
        if self.settings.ntfy_topic:
            self.host.notify(self.settings.ntfy_topic, message)

    def gh(self, *args: str) -> tuple[int, str]:
        return self.host.run(["gh", *args, "--repo", REPO])

    def gh_json(self, *args: str) -> Any:
        code, out = self.gh(*args)
        if code != 0:
            raise RuntimeError(f"gh {' '.join(args)} failed: {out.strip()}")
        return json.loads(out)


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
    return Settings(concurrency=int(raw), ntfy_topic=values.get("NTFY_TOPIC", ""))


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


def loop_pull_requests(tick: Tick) -> list[dict[str, Any]]:
    fields = "number,state,body,labels,headRefName,commits,comments,statusCheckRollup"
    found = tick.gh_json("pr", "list", "--state", "all", "--limit", "40", "--json", fields)
    return [pr for pr in found if MARKER in (pr.get("body") or "")]


def closes(pr: dict[str, Any]) -> int | None:
    match = re.search(r"Closes #(\d+)", pr.get("body") or "")
    return int(match.group(1)) if match else None


def names(item: dict[str, Any]) -> set[str]:
    return {label["name"] for label in item.get("labels") or []}


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
    if USAGE_LIMIT.search(tail) and outcome != "0":
        if kind == "issue":
            tick.gh("issue", "edit", number, "--add-label", "agent:ready",
                    "--remove-label", "agent:running")
        remove_worktree(tick, worktree)
        until = tick.host.now() + PAUSE_SECONDS
        (tick.home / "paused-until").write_text(str(int(until)))
        tick.say(f"{key}: plan limit reached, paused 60 minutes")
        tick.notify(f"ReviewRadar loop paused 60 minutes: plan limit reached ({key})")
        return
    if outcome == "0":
        remove_worktree(tick, worktree)
        tick.say(f"{key}: ended normally")
        return
    reason = {"timeout": "stopped after 45 minutes", "gone": "stopped with no exit code"}.get(
        outcome, f"ended with error {outcome}"
    )
    if kind == "pr":
        tick.say(f"{key}: {reason}; worktree kept")
        tick.notify(f"ReviewRadar build for pull request #{number} {reason}")
        return
    labels = names(tick.gh_json("issue", "view", number, "--json", "labels"))
    has_pr = any(closes(pr) == int(number) for pr in prs)
    if "agent:running" not in labels or has_pr:
        remove_worktree(tick, worktree)
        tick.say(f"{key}: {reason}, but the build already handed over")
        return
    ensure_label(tick, "agent:failed")
    tick.gh("issue", "edit", number, "--add-label", "agent:failed", "--remove-label",
            "agent:running")
    body = f"{MARKER}\nThe loop build {reason}. Last {LOG_TAIL} lines of the log:\n"
    body += f"\n```\n{tail}\n```"
    tick.gh("issue", "comment", number, "--body", body)
    tick.say(f"{key}: {reason}; agent:failed, worktree kept")
    tick.notify(f"ReviewRadar build for issue #{number} failed: {reason}")


def remove_worktree(tick: Tick, worktree: Path) -> None:
    if worktree.exists():
        tick.host.run(["git", "-C", str(REPO_ROOT), "worktree", "remove", str(worktree)])


def ensure_label(tick: Tick, label: str) -> None:
    existing = {item["name"] for item in tick.gh_json("label", "list", "--json", "name",
                                                      "--limit", "200")}
    if label not in existing:
        color, description = LABEL_COLORS[label]
        tick.gh("label", "create", label, "--color", color, "--description", description)


def owner_redo_after(comments: list[dict[str, Any]], since: str) -> bool:
    return any(
        (c.get("author") or {}).get("login") == OWNER
        and (c.get("body") or "").startswith("/redo")
        and MARKER not in (c.get("body") or "")
        and (c.get("createdAt") or "") > since
        for c in comments
    )


def pr_needs_run(tick: Tick, pr: dict[str, Any], review_issues: set[int]) -> bool:
    """AC4: the cases of work-queue section 1."""
    labels = names(pr)
    if pr["state"] != "OPEN":
        return bool(labels & PR_LABELS) or closes(pr) in review_issues
    commits = pr.get("commits") or []
    last_commit = commits[-1].get("committedDate", "") if commits else ""
    comments = list(pr.get("comments") or [])
    issue = closes(pr)
    if issue is not None:
        comments += tick.gh_json("issue", "view", str(issue), "--json", "comments")["comments"]
    if owner_redo_after(comments, last_commit):
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


def runs_alone(issue: dict[str, Any]) -> bool:
    body = issue.get("body") or ""
    return "risk:high" in names(issue) or any(word in body for word in ALONE_WORDS)


def choose(tick: Tick, prs: list[dict[str, Any]], running: dict[str, bool]) -> list[Target]:
    """AC3 to AC6: pull requests first, then the oldest ready issues, within the free slots."""
    free = tick.settings.concurrency - len(running)
    chosen: list[Target] = []
    if free <= 0:
        return chosen
    reviews = tick.gh_json("issue", "list", "--state", "all", "--label", "agent:review",
                           "--limit", "200", "--json", "number")
    review_issues = {item["number"] for item in reviews}
    for pr in prs:
        key = f"pr-{pr['number']}"
        if len(chosen) < free and key not in running and pr_needs_run(tick, pr, review_issues):
            prompt = f"Use the work-queue skill for pull request #{pr['number']} only."
            chosen.append(Target(key, pr["number"], prompt, branch=pr["headRefName"]))
    if any(running.values()):
        return chosen
    issues = tick.gh_json("issue", "list", "--state", "open", "--limit", "200",
                          "--json", "number,body,labels,createdAt")
    open_numbers = {item["number"] for item in issues}
    waiting = sum(1 for pr in prs if pr["state"] == "OPEN")
    waiting += sum(1 for item in issues if "agent:running" in names(item))
    ready = sorted((i for i in issues if "agent:ready" in names(i)),
                   key=lambda i: (i["createdAt"], i["number"]))
    for issue in ready:
        if len(chosen) >= free or waiting >= WAITING_CAP:
            break
        key = f"issue-{issue['number']}"
        depends = {int(n) for n in re.findall(r"Depends on #(\d+)", issue.get("body") or "")}
        if key in running or names(issue) & SKIP_LABELS or depends & open_numbers:
            continue
        if not labelled_by_owner(tick, issue["number"]):
            tick.say(f"{key}: agent:ready was not added by {OWNER}; skipped")
            continue
        prompt = f"Use the work-queue skill for issue #{issue['number']} only."
        if runs_alone(issue):
            if running or chosen:
                break
            chosen.append(Target(key, issue["number"], prompt, alone=True))
            break
        chosen.append(Target(key, issue["number"], prompt))
        waiting += 1
    return chosen


def start(tick: Tick, target: Target) -> bool:
    """AC7 to AC9: worktree, uv sync, claim, then the build in the background."""
    worktree = tick.home / "worktrees" / target.key
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git = ["git", "-C", str(REPO_ROOT)]
    if worktree.exists():
        aside = worktree.with_name(f"{target.key}-{int(tick.host.now())}")
        tick.host.run([*git, "worktree", "move", str(worktree), str(aside)])
    tick.host.run([*git, "fetch", "origin", "main", *([target.branch] if target.branch else [])])
    if target.branch:
        add = [*git, "worktree", "add", "-B", target.branch, str(worktree),
               f"origin/{target.branch}"]
    else:
        add = [*git, "worktree", "add", "--detach", str(worktree), "origin/main"]
    lab = worktree / "claude-code-training-lab"
    for step, cwd in ((add, None), (["uv", "sync", "--frozen"], lab)):
        code, out = tick.host.run(step, cwd=cwd)
        if code != 0:
            tick.say(f"{target.key}: not started, {' '.join(step[:4])} failed: {out.strip()}")
            return False
    if target.key.startswith("issue-"):
        ensure_label(tick, "agent:running")
        tick.gh("issue", "edit", str(target.number), "--add-label", "agent:running")
    run = tick.runs / target.key
    run.mkdir(parents=True, exist_ok=True)
    if target.alone:
        (run / "alone").touch()
    wrapper = [sys.executable, str(Path(__file__).resolve()), "run", str(run), str(lab),
               target.prompt]
    pid = tick.host.spawn(wrapper, run / "log.txt")
    (run / "pid").write_text(str(pid))
    tick.say(f"{target.key}: started (pid {pid})")
    return True


def paused(tick: Tick) -> bool:
    flag = tick.home / "paused-until"
    return flag.exists() and float(flag.read_text().strip() or 0) > tick.host.now()


def queue_empty(tick: Tick, prs: list[dict[str, Any]]) -> None:
    """AC12: one 'queue empty' message, again only after something changed."""
    waiting = sum(1 for pr in prs if pr["state"] == "OPEN")
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
        prs = loop_pull_requests(tick)
        finish_runs(tick, prs)
        running = running_keys(tick)
        if paused(tick):
            tick.say("paused after the plan limit; no build started")
            return tick.log
        started = [t for t in choose(tick, prs, running) if start(tick, t)]
        if started:
            (home / "last-empty").unlink(missing_ok=True)
        elif not running:
            queue_empty(tick, prs)
    finally:
        lock.rmdir()
    return tick.log


def run_build(run: Path, folder: Path, prompt: str) -> str:
    """The background wrapper: one `claude -p`, stopped after 45 minutes; writes the outcome."""
    env = {**os.environ, "REVIEWRADAR_LOOP": "1"}
    args = ["claude", "-p", prompt, "--max-turns", str(MAX_TURNS)]
    child = subprocess.Popen(
        args, cwd=folder, env=env, stdin=subprocess.DEVNULL, start_new_session=True
    )
    try:
        outcome = str(child.wait(timeout=RUN_LIMIT))
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
        outcome = "timeout"
    (run / "exit").write_text(outcome)
    return outcome


def main(argv: list[str]) -> int:
    if argv[:1] == ["run"] and len(argv) == 4:
        run_build(Path(argv[1]), Path(argv[2]), argv[3])
        return 0
    home = Path(os.environ.get("REVIEWRADAR_HOME", Path.home() / ".reviewradar"))
    home.mkdir(parents=True, exist_ok=True)
    tick_once(RealHost(), home)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
