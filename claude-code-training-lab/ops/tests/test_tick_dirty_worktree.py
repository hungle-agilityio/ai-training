"""A file a build left modified never holds a branch, and a green pull request gets its label."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ops import agent_tick
from ops.tests.test_agent_tick import NOW, FakeHost, comment, pull

LINK = "https://claude.ai/artifact/abc"
PATCH = "diff --git a/x.py b/x.py\n"


class DirtyHost(FakeHost):
    """Plain `git worktree remove` fails, as git does for a worktree with modified files."""

    force_fails: bool = False
    diff_fails: bool = False

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[3:5] == ["worktree", "remove"]:
            self.calls.append(args)
            if "--force" not in args:
                return 1, "contains modified or untracked files, use --force to delete it"
            return (1, "locked") if self.force_fails else (0, "")
        if args[3:4] == ["diff"]:
            self.calls.append(args)
            return (1, "boom") if self.diff_fails else (0, PATCH)
        return super().run(args, cwd)


def make_tick(tmp_path: Path, host: FakeHost) -> agent_tick.Tick:
    return agent_tick.Tick(host, tmp_path, agent_tick.Settings(concurrency=1, ntfy_topic="t"))


def worktree_of(tmp_path: Path, name: str = "issue-9") -> Path:
    folder = tmp_path / "worktrees" / name
    folder.mkdir(parents=True)
    return folder


def forced(host: FakeHost) -> list[list[str]]:
    return [c for c in host.calls if c[3:6] == ["worktree", "remove", "--force"]]


def green(number: int, *labels: str, link: str = LINK, checks: str = "SUCCESS") -> dict[str, Any]:
    pr = pull(number, *labels, closes=number + 100, checks=checks)
    pr["body"] += f"\nVerify report: {link}"
    pr["createdAt"] = "2026-10-20T00:00:00Z"
    return pr


def added_labels(host: FakeHost) -> list[list[str]]:
    return [c[:6] for c in host.calls if c[:3] == ["gh", "pr", "edit"] and "--add-label" in c]


def test_a_handed_over_worktree_with_a_stray_file_is_saved_and_removed(tmp_path: Path) -> None:
    host = DirtyHost(clock=NOW)
    tick = make_tick(tmp_path, host)
    folder = worktree_of(tmp_path)

    agent_tick.remove_worktree(tick, folder, handed_over=True)

    patch = tmp_path / "archive" / f"issue-9-{int(NOW)}.patch"
    assert patch.read_text() == PATCH
    assert len(forced(host)) == 1
    assert f"issue-9: uncommitted changes saved to {patch}, worktree removed" in tick.log


def test_untracked_files_are_in_the_saved_patch(tmp_path: Path) -> None:
    host = DirtyHost(clock=NOW)
    tick = make_tick(tmp_path, host)

    agent_tick.remove_worktree(tick, worktree_of(tmp_path), handed_over=True)

    assert any(c[3:5] == ["add", "-A"] for c in host.calls)
    assert any(c[3:] == ["diff", "--cached", "--binary", "HEAD"] for c in host.calls)


def test_a_worktree_is_never_forced_when_the_patch_cannot_be_saved(tmp_path: Path) -> None:
    host = DirtyHost(clock=NOW)
    host.diff_fails = True
    tick = make_tick(tmp_path, host)

    agent_tick.remove_worktree(tick, worktree_of(tmp_path), handed_over=True)

    assert forced(host) == []
    assert any("worktree not removed" in line for line in tick.log)


def test_a_failed_forced_removal_is_logged(tmp_path: Path) -> None:
    host = DirtyHost(clock=NOW)
    host.force_fails = True
    tick = make_tick(tmp_path, host)

    agent_tick.remove_worktree(tick, worktree_of(tmp_path), handed_over=True)

    assert "issue-9: worktree not removed (locked)" in tick.log


def test_a_build_that_did_not_hand_over_keeps_its_work(tmp_path: Path) -> None:
    host = DirtyHost(clock=NOW)
    tick = make_tick(tmp_path, host)

    agent_tick.remove_worktree(tick, worktree_of(tmp_path), handed_over=False)

    assert forced(host) == []
    assert not (tmp_path / "archive").exists()
    assert any("worktree kept" in line for line in tick.log)


def test_a_clean_worktree_needs_no_patch(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    tick = make_tick(tmp_path, host)

    agent_tick.remove_worktree(tick, worktree_of(tmp_path), handed_over=True)

    assert not (tmp_path / "archive").exists()
    assert tick.log == []


def test_a_green_pull_request_without_a_label_is_marked_ready(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    tick = make_tick(tmp_path, host)
    prs = [green(5)]

    agent_tick.mark_green_ready(tick, prs, {})

    assert added_labels(host) == [["gh", "pr", "edit", "5", "--add-label", "pr:ready-for-review"]]
    assert agent_tick.names(prs[0]) == {"pr:ready-for-review"}
    assert "pr-5: CI is green and the report is linked; pr:ready-for-review" in tick.log
    assert agent_tick.pr_needs_run(tick, prs[0]) is False


def test_a_pull_request_needs_a_report_link_to_be_marked(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    pr = pull(5, closes=105)

    agent_tick.mark_green_ready(make_tick(tmp_path, host), [pr], {})

    assert added_labels(host) == []


def test_red_running_or_missing_checks_are_not_marked(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    red = green(5, checks="FAILURE")
    running = green(6)
    running["statusCheckRollup"] = [{"status": "IN_PROGRESS"}]
    missing = green(7)
    missing["statusCheckRollup"] = []

    agent_tick.mark_green_ready(make_tick(tmp_path, host), [red, running, missing], {})

    assert added_labels(host) == []


def test_a_pull_request_with_a_status_label_is_left_alone(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)

    agent_tick.mark_green_ready(make_tick(tmp_path, host), [green(5, "pr:blocked")], {})

    assert added_labels(host) == []


def test_a_pull_request_with_an_open_change_request_is_not_marked(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    pr = green(5)
    pr["comments"] = [comment("/redo please change this")]

    agent_tick.mark_green_ready(make_tick(tmp_path, host), [pr], {})

    assert added_labels(host) == []


def test_a_running_build_keeps_the_label_for_itself(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    tick = make_tick(tmp_path, host)

    agent_tick.mark_green_ready(tick, [green(5)], {"pr-5": False})
    agent_tick.mark_green_ready(tick, [green(6)], {"issue-106": False})

    assert added_labels(host) == []


def test_a_merged_pull_request_is_not_marked(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW)
    pr = green(5)
    pr["state"] = "MERGED"

    agent_tick.mark_green_ready(make_tick(tmp_path, host), [pr], {})

    assert added_labels(host) == []


def test_a_failed_label_call_leaves_the_pull_request_for_a_build(tmp_path: Path) -> None:
    host = FakeHost(clock=NOW, fail="--add-label")
    tick = make_tick(tmp_path, host)
    prs = [green(5)]

    agent_tick.mark_green_ready(tick, prs, {})

    assert agent_tick.names(prs[0]) == set()
    assert agent_tick.pr_needs_run(tick, prs[0]) is True
