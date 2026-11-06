"""The tick removes the kept worktrees of closed work (#255)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ops import agent_tick
from ops.tests.test_agent_tick import NOW, FakeHost, issue


class BranchHost(FakeHost):
    """Answers `git branch --show-current` per folder; `fail_remove` names folders that fail."""

    branches: dict[str, str]
    fail_remove: set[str]

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[3:5] == ["branch", "--show-current"]:
            self.calls.append(args)
            return 0, getattr(self, "branches", {}).get(Path(args[2]).name, "")
        if args[3:5] == ["worktree", "remove"] and Path(args[-1]).name in getattr(
            self, "fail_remove", set()
        ):
            self.calls.append(args)
            return 1, "locked"
        return super().run(args, cwd)


def tidy(
    tmp_path: Path,
    names: list[str],
    host: BranchHost,
    prs: list[dict[str, Any]] | None = None,
    running: dict[str, bool] | None = None,
) -> list[str]:
    for name in names:
        (tmp_path / "worktrees" / name).mkdir(parents=True)
    tick = agent_tick.Tick(host, tmp_path, agent_tick.Settings(concurrency=1, ntfy_topic="t"))
    agent_tick.tidy_worktrees(tick, prs or [], running or {})
    return tick.log


def removed(host: BranchHost) -> list[str]:
    return [Path(c[-1]).name for c in host.calls if c[3:6] == ["worktree", "remove", "--force"]]


def renames(host: BranchHost) -> list[list[str]]:
    return [c[5:] for c in host.calls if c[3:5] == ["branch", "-m"]]


def test_a_closed_issue_loses_its_worktree_and_its_branch_is_archived(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW, issues=[issue(2)])
    host.branches = {"issue-1": "task/1-thing"}
    log = tidy(tmp_path, ["issue-1", "issue-2"], host)
    assert removed(host) == ["issue-1"]
    assert renames(host) == [["task/1-thing", f"archive/task/1-thing-{int(NOW)}"]]
    assert "issue-1: closed, worktree removed" in log


def test_a_closed_or_merged_pull_request_loses_its_worktree(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW)
    prs = [{"number": 3, "state": "MERGED"}, {"number": 4, "state": "CLOSED"}]
    tidy(tmp_path, ["pr-3", "pr-4"], host, prs)
    assert removed(host) == ["pr-3", "pr-4"]


def test_open_work_and_running_builds_keep_their_worktree(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW, issues=[issue(2)])
    prs = [{"number": 3, "state": "OPEN"}]
    tidy(tmp_path, ["issue-2", "pr-3", "issue-9"], host, prs, running={"issue-9": False})
    assert removed(host) == []
    assert renames(host) == []


def test_a_moved_aside_folder_goes_after_three_days_whatever_the_state(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW, issues=[issue(5)])
    old = f"issue-5-{int(NOW) - 3 * 86400 - 1}"
    fresh = f"issue-5-{int(NOW) - 3 * 86400 + 60}"
    log = tidy(tmp_path, [old, fresh], host)
    assert removed(host) == [old]
    assert f"{old}: moved aside more than 3 days ago, worktree removed" in log


def test_a_detached_worktree_is_removed_without_a_rename(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW)
    host.branches = {"issue-1": ""}
    tidy(tmp_path, ["issue-1"], host)
    assert removed(host) == ["issue-1"]
    assert renames(host) == []


def test_at_most_ten_folders_are_removed_per_tick(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW)
    tidy(tmp_path, [f"issue-{n}" for n in range(1, 16)], host)
    assert len(removed(host)) == 10


def test_a_failed_removal_is_logged_and_the_tick_goes_on(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW)
    host.fail_remove = {"issue-1"}
    log = tidy(tmp_path, ["issue-1", "issue-2"], host)
    assert removed(host) == ["issue-1", "issue-2"]
    assert any(line.startswith("issue-1: worktree not removed") for line in log)
    assert "issue-2: closed, worktree removed" in log


def test_no_branch_is_ever_deleted(tmp_path: Path) -> None:
    host = BranchHost(clock=NOW)
    host.branches = {"issue-1": "task/1-thing"}
    tidy(tmp_path, ["issue-1"], host)
    assert not any(c[3:5] in (["branch", "-d"], ["branch", "-D"]) for c in host.calls)
