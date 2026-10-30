"""Cut a sprint release: branch `release/sprint-N`, a date tag, and `deploy` moved to the commit.

Run by hand on the Mac mini: `uv run python ops/release.py [--dry-run]`.
Spec: specs/release-deploy/spec.md (AC4 to AC9). It never forces a push, never pushes `main`
and never changes an existing release ref.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEPLOY = "deploy"
SPRINT_PREFIX = "release/sprint-"
VIETNAM = ZoneInfo("Asia/Ho_Chi_Minh")
RENDER_LINE = "Render deploys branch deploy after Checks pass."
PR_NUMBER = re.compile(r"#(\d+)")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Refusal(Exception):
    """The release must not happen; the message is the one line shown to the owner."""


@dataclass(frozen=True)
class Plan:
    sha: str
    title: str
    branch: str
    tag: str
    pull_requests: tuple[str, ...]


def git(args: Sequence[str], cwd: Path, check: bool = True) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)
    return done.stdout.strip()


def latest_checks(sha: str, cwd: Path) -> str | None:
    """The newest `Checks` run of a commit: "success", another conclusion, "running" or None."""
    done = subprocess.run(
        ["gh", "run", "list", "--workflow", "Checks", "--commit", sha, "--limit", "1",
         "--json", "status,conclusion"],
        cwd=cwd, capture_output=True, text=True, check=True,
    )
    runs = json.loads(done.stdout or "[]")
    if not runs:
        return None
    if runs[0]["status"] != "completed":
        return "running"
    return str(runs[0]["conclusion"] or "failure")


def remote_names(cwd: Path, kind: str) -> set[str]:
    out = git(["ls-remote", "--" + kind, "origin"], cwd)
    return {line.split("\t")[1].split("/", 2)[2] for line in out.splitlines() if "\t" in line}


def next_branch(branches: set[str]) -> str:
    numbers = [int(b[len(SPRINT_PREFIX):]) for b in branches
               if b.startswith(SPRINT_PREFIX) and b[len(SPRINT_PREFIX):].isdigit()]
    return SPRINT_PREFIX + str(max(numbers, default=0) + 1)


def next_tag(tags: set[str], now: datetime) -> str:
    base = "v" + now.astimezone(VIETNAM).strftime("%Y.%m.%d")
    tag, count = base, 1
    while tag in tags:
        count += 1
        tag = base + "." + str(count)
    return tag


def merged_pull_requests(cwd: Path, since: str | None, sha: str) -> tuple[str, ...]:
    span = since + ".." + sha if since else sha
    out = git(["log", "--merges", "--first-parent", "--reverse",
               "--format=%s%x00%b%x1e", span], cwd)
    lines: list[str] = []
    for record in out.split("\x1e"):
        subject, _, body = record.strip().partition("\x00")
        found = PR_NUMBER.search(subject)
        if not found:
            continue
        title = next((ln.strip() for ln in body.splitlines() if ln.strip()), subject)
        lines.append("#" + found.group(1) + " " + title)
    return tuple(lines)


def make_plan(cwd: Path, now: datetime) -> Plan:
    git(["fetch", "origin"], cwd)
    sha = git(["rev-parse", "origin/main"], cwd)
    short = sha[:7]
    status = latest_checks(sha, cwd)
    if status is None:
        raise Refusal("no Checks run found for " + short)
    if status == "running":
        raise Refusal("Checks are still running for " + short)
    if status != "success":
        raise Refusal("Checks did not succeed for " + short + " (" + status + ")")
    deploy = git(["rev-parse", "--verify", "-q", "refs/remotes/origin/" + DEPLOY], cwd, check=False)
    if deploy == sha:
        raise Refusal("nothing new to release")
    if deploy:
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", deploy, sha], cwd=cwd)
        if ancestor.returncode != 0:
            raise Refusal("origin/" + DEPLOY + " is not an ancestor of " + short)
    tags = remote_names(cwd, "tags") | set(git(["tag", "-l"], cwd).splitlines())
    return Plan(
        sha=sha,
        title=git(["log", "-1", "--format=%s", sha], cwd),
        branch=next_branch(remote_names(cwd, "heads")),
        tag=next_tag(tags, now),
        pull_requests=merged_pull_requests(cwd, deploy or None, sha),
    )


def describe(plan: Plan) -> list[str]:
    lines = ["Commit: " + plan.sha[:7] + " " + plan.title, "Branch: " + plan.branch,
             "Tag: " + plan.tag, "Merged pull requests:"]
    return lines + (["  " + pr for pr in plan.pull_requests] or ["  (none)"])


def push(plan: Plan, cwd: Path) -> None:
    git(["tag", "-a", plan.tag, plan.sha, "-m", plan.branch], cwd)
    try:
        git(["push", "--atomic", "origin",
             plan.sha + ":refs/heads/" + plan.branch,
             "refs/tags/" + plan.tag + ":refs/tags/" + plan.tag,
             plan.sha + ":refs/heads/" + DEPLOY], cwd)
    except subprocess.CalledProcessError:
        git(["tag", "-d", plan.tag], cwd, check=False)
        raise


def main(argv: Sequence[str] | None = None, cwd: Path = PROJECT_ROOT,
         now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cut a sprint release for Render.")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, push nothing")
    args = parser.parse_args(argv)
    try:
        plan = make_plan(cwd, now or datetime.now(VIETNAM))
        if args.dry_run:
            print("\n".join(describe(plan)))
            return 0
        push(plan, cwd)
    except Refusal as refusal:
        print(str(refusal), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as failure:
        detail = (failure.stderr or "").strip().splitlines()
        print("git or gh failed: " + (detail[-1] if detail else str(failure.cmd)), file=sys.stderr)
        return 1
    print("\n".join(describe(plan)))
    print(RENDER_LINE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
