"""Guards for parallel builds: dependencies, shared files, red main. Run: uv run pytest ops/tests"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, issue, started

GREEN = [{"conclusion": "success", "headSha": "a" * 40, "url": "https://ci/1"}]
RED = [{"conclusion": "failure", "headSha": "b1c2d3e4f5" + "0" * 30, "url": "https://ci/2"}]


@dataclass
class ChecksHost(FakeHost):
    """FakeHost that also answers the Checks run list of main."""

    main_runs: Any = None
    main_fails: bool = False

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[:3] == ["gh", "run", "list"]:
            self.calls.append(args)
            if self.main_fails:
                return 1, "HTTP 502"
            return 0, json.dumps(GREEN if self.main_runs is None else self.main_runs)
        return super().run(args, cwd)


def files(*paths: str) -> str:
    return "## Files likely touched\n\n" + "\n".join(f"- `{p}`" for p in paths) + "\n\n## Next\n"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=3\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def prompt(n: int) -> str:
    return f"Use the work-queue skill for issue #{n} only."


# AC1: every Depends on number


def test_depends_on_reads_every_number_on_the_line() -> None:
    body = "Depends on #63, #61 (both change settings.py)\nDepends on #7\nSee #99"
    assert agent_tick.depends_on(body) == {63, 61, 7}


def test_issue_waits_while_any_dependency_is_open(home: Path) -> None:
    host = ChecksHost(issues=[
        issue(1, "agent:ready", body="Depends on #63, #61\n" + files("ops/a.py")),
        issue(61, "agent:manual"),
    ])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_issue_starts_when_all_dependencies_are_closed(home: Path) -> None:
    host = ChecksHost(issues=[issue(1, "agent:ready", body="Depends on #63, #61\n" + files("x"))])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]


# AC2: files of an issue


def test_files_strip_notes_and_prefixes() -> None:
    body = (
        "## Files likely touched\n\n- `claude-code-training-lab/reviews/services.py`\n"
        "- `./ops/README.md` (only one line)\n- `ops/tests/test_x.py` (NEW)\n"
        "not a bullet `skip.py`\n\n## Depends on\n- `later.py`\n"
    )
    assert agent_tick.files_of(body) == {
        "reviews/services.py", "ops/README.md", "ops/tests/test_x.py",
    }


# AC3: wait on shared files


def test_two_ready_issues_sharing_a_file_do_not_start_together(home: Path) -> None:
    host = ChecksHost(issues=[
        issue(1, "agent:ready", body=files("reviews/services.py", "reviews/a.py")),
        issue(2, "agent:ready", body=files("claude-code-training-lab/reviews/services.py")),
        issue(3, "agent:ready", body=files("reviews/views.py")),
    ])
    log = agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1), prompt(3)]
    assert "issue-2: waits for #1, which also touches reviews/services.py" in log


def test_ready_issue_overlapping_an_issue_in_review_waits(home: Path) -> None:
    host = ChecksHost(issues=[
        issue(5, "agent:review", body=files("reviews/services.py")),
        issue(6, "agent:ready", body=files("reviews/services.py")),
    ])
    log = agent_tick.tick_once(host, home)
    assert host.spawned == []
    assert "issue-6: waits for #5, which also touches reviews/services.py" in log


def test_a_file_shared_with_a_closed_issue_is_no_clash(home: Path) -> None:
    host = ChecksHost(issues=[
        issue(5, "agent:review", body=files("reviews/services.py")) | {"closed": True},
        issue(6, "agent:ready", body=files("reviews/services.py")),
    ])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(6)]


# AC4: no files listed runs alone


def test_issue_without_the_section_runs_alone(home: Path) -> None:
    host = ChecksHost(issues=[
        issue(1, "agent:ready", body="## Summary\nNo files here."),
        issue(2, "agent:ready", body=files("ops/b.py")),
    ])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]


def test_section_without_a_backticked_path_runs_alone() -> None:
    body = "## Files likely touched\n\nops/agent_tick.py, ops/README.md\n"
    assert agent_tick.runs_alone(issue(1, "agent:ready", body=body))


# AC5: red main


def test_red_main_starts_no_new_issue_and_sends_once_per_commit(home: Path) -> None:
    host = ChecksHost(main_runs=RED, issues=[issue(1, "agent:ready", body=files("a.py"))])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert host.spawned == []
    red = [m for m in host.sent if "main is red" in m]
    assert red == ["rr-test: main is red at b1c2d3e: https://ci/2"]


def test_a_new_red_commit_sends_again(home: Path) -> None:
    host = ChecksHost(main_runs=RED)
    agent_tick.tick_once(host, home)
    host.main_runs = [dict(RED[0], headSha="c" * 40)]
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "main is red" in m]) == 2


def test_red_main_still_runs_pull_requests(home: Path) -> None:
    from ops.tests.test_agent_tick import pull

    host = ChecksHost(main_runs=RED, prs=[pull(20, closes=5)],
                      issues=[issue(1, "agent:ready", body=files("a.py"))])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for pull request #20 only."]


def test_green_main_starts_issues(home: Path) -> None:
    host = ChecksHost(main_runs=GREEN, issues=[issue(1, "agent:ready", body=files("a.py"))])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]


def test_unreadable_main_run_counts_as_green_with_a_log_line(home: Path) -> None:
    host = ChecksHost(main_fails=True, issues=[issue(1, "agent:ready", body=files("a.py"))])
    log = agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]
    assert "main checks could not be read; going on as if main were green" in log
