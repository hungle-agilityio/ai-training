"""A message for every loop step, on ntfy and Slack. Run: uv run pytest ops/tests --no-cov"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, add_run, comment, issue, pull

HOOK = "https://hooks.slack.com/services/T000/B000/SECRETxyz"


@dataclass
class NotifyHost(FakeHost):
    """FakeHost with a Slack webhook and git answers for the main checkout."""

    slack_sent: list[str] = field(default_factory=list)
    slack_ok: bool = True
    git: dict[str, tuple[int, str]] = field(default_factory=dict)

    def slack(self, url: str, message: str) -> bool:
        self.slack_sent.append(message)
        return self.slack_ok

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[0] == "git":
            self.calls.append(args)
            text = " ".join(args)
            return next((a for part, a in self.git.items() if part in text), (0, ""))
        return super().run(args, cwd)


ON_MAIN = {"branch --show-current": (0, "main\n"), "rev-parse --short HEAD": (0, "abc1234\n")}


def make_home(tmp_path: Path, env: str = "NTFY_TOPIC=rr-test\n") -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\n" + env)
    return tmp_path


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return make_home(tmp_path)


def titled(number: int, *labels: str, title: str = "Fix the thing") -> dict[str, Any]:
    return issue(number, *labels) | {"title": title}


def messages(host: FakeHost, text: str) -> list[str]:
    return [m.split(": ", 1)[1] for m in host.sent if text in m]


# AC1: build started


def test_issue_start_names_the_issue(home: Path) -> None:
    host = NotifyHost(issues=[titled(4, "agent:ready", title="Raise the limit")])
    agent_tick.tick_once(host, home)
    assert messages(host, "started") == ["ReviewRadar started #4: Raise the limit"]


def test_pull_request_start_counts_change_requests(home: Path) -> None:
    redo = comment("/redo rename it")
    host = NotifyHost(prs=[pull(20, "pr:ready-for-review", closes=5, comments=[redo])],
                      issue_comments={5: [comment("/redo add a test")]})
    agent_tick.tick_once(host, home)
    assert messages(host, "working on") == [
        "ReviewRadar working on PR #20 (2 change requests open)"
    ]


def test_pull_request_start_without_change_request_says_ci(home: Path) -> None:
    host = NotifyHost(prs=[pull(20, closes=5)])
    agent_tick.tick_once(host, home)
    assert messages(host, "working on") == ["ReviewRadar working on PR #20 (CI)"]


# AC2: needs you


def test_blocked_is_sent_once_per_head_and_again_after_a_commit(home: Path) -> None:
    pr = pull(20, "pr:blocked", closes=5)
    pr["commits"] = [{"oid": "a1", "committedDate": "2026-10-20T10:00:00Z"}]
    host = NotifyHost(prs=[pr])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert messages(host, "needs you") == [
        "ReviewRadar PR #20 needs you: pr:blocked\n"
        "https://github.com/hungle-agilityio/ai-training/pull/20"
    ]
    pr["commits"].append({"oid": "b2", "committedDate": "2026-10-21T10:00:00Z"})
    agent_tick.tick_once(host, home)
    assert len(messages(host, "needs you")) == 2


def test_ci_failed_needs_you(home: Path) -> None:
    host = NotifyHost(prs=[pull(21, "pr:ci-failed", closes=6)])
    agent_tick.tick_once(host, home)
    assert messages(host, "needs you")[0].startswith("ReviewRadar PR #21 needs you: pr:ci-failed")


# AC3: waiting on the cap, or queue empty


def test_cap_reached_sends_waiting_once(home: Path) -> None:
    prs = [pull(n, "pr:ready-for-review") for n in range(20, 30)]
    host = NotifyHost(prs=prs, issues=[issue(1, "agent:ready"), issue(2, "agent:ready")])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert messages(host, "waiting") == [
        "ReviewRadar waiting: 10 pull requests open (limit 10), 2 ready issues not started\n"
        + agent_tick.OPEN_PRS_URL
    ]
    assert messages(host, "queue empty") == []


def test_no_ready_issue_sends_queue_empty(home: Path) -> None:
    host = NotifyHost(issues=[issue(1, "agent:review")])
    agent_tick.tick_once(host, home)
    assert messages(host, "queue empty") == ["ReviewRadar queue empty, 0 pull requests waiting"]


# AC4: merged


def test_merged_pull_request_is_announced_once_with_the_new_sha(home: Path) -> None:
    (home / "announced-merged").write_text("")
    host = NotifyHost(prs=[pull(20, state="MERGED", closes=5)], git=dict(ON_MAIN))
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert messages(host, "merged") == ["ReviewRadar PR #20 merged (#5); main is now abc1234"]
    pull_index = next(i for i, c in enumerate(host.calls) if "merge" in c and "--ff-only" in c)
    sha_index = next(i for i, c in enumerate(host.calls) if "rev-parse" in c)
    assert pull_index < sha_index


def test_merged_while_main_cannot_be_pulled_says_why(home: Path) -> None:
    (home / "announced-merged").write_text("")
    host = NotifyHost(prs=[pull(20, state="MERGED", closes=5)],
                      git={"branch --show-current": (0, "task/9-x\n")})
    agent_tick.tick_once(host, home)
    assert messages(host, "PR #20 merged") == [
        "ReviewRadar PR #20 merged (#5); main checkout not updated: the checkout is on task/9-x"
    ]


def test_first_run_records_merged_pull_requests_and_sends_nothing(home: Path) -> None:
    host = NotifyHost(prs=[pull(20, state="MERGED", closes=5), pull(19, state="MERGED")])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert messages(host, "merged") == []
    assert set((home / "announced-merged").read_text().split()) == {"19", "20"}


# AC5, AC6: channels


def test_no_topic_and_no_slack_sends_nothing(tmp_path: Path) -> None:
    home = make_home(tmp_path, "")
    host = NotifyHost(issues=[titled(4, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert host.sent == [] and host.slack_sent == []


def test_slack_only(tmp_path: Path) -> None:
    home = make_home(tmp_path, f"SLACK_WEBHOOK_URL={HOOK}\n")
    host = NotifyHost(issues=[titled(4, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert host.sent == []
    assert host.slack_sent == ["ReviewRadar started #4: Fix the thing"]


def test_ntfy_only(home: Path) -> None:
    host = NotifyHost(issues=[titled(4, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert host.slack_sent == [] and host.sent == ["rr-test: ReviewRadar started #4: Fix the thing"]


def test_both_channels_get_every_message(tmp_path: Path) -> None:
    home = make_home(tmp_path, f"NTFY_TOPIC=rr-test\nSLACK_WEBHOOK_URL={HOOK}\n")
    add_run(home, "issue-1", 77, exit_text="1", log="boom")
    host = NotifyHost(issues=[issue(1, "agent:running")])
    agent_tick.tick_once(host, home)
    assert [m.split(": ", 1)[1] for m in host.sent] == host.slack_sent
    assert any("failed" in m for m in host.slack_sent)


def test_failed_slack_post_logs_without_the_url_and_keeps_ntfy(tmp_path: Path) -> None:
    home = make_home(tmp_path, f"NTFY_TOPIC=rr-test\nSLACK_WEBHOOK_URL={HOOK}\n")
    host = NotifyHost(issues=[titled(4, "agent:ready")], slack_ok=False)
    log = agent_tick.tick_once(host, home)
    assert "Slack post failed" in log
    assert not any("hooks.slack.com" in line or "SECRET" in line for line in log)
    assert host.sent == ["rr-test: ReviewRadar started #4: Fix the thing"]


def test_real_slack_failure_prints_no_url(capsys: pytest.CaptureFixture[str],
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise OSError(f"cannot reach {HOOK}")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    assert agent_tick.RealHost().slack(HOOK, "hi") is False
    out = capsys.readouterr().out
    assert "Slack post failed (OSError)" in out and "SECRET" not in out


def test_env_example_has_an_empty_slack_line() -> None:
    example = Path(agent_tick.__file__).with_name("agent.env.example").read_text()
    assert "\nSLACK_WEBHOOK_URL=\n" in example
