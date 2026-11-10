"""#408: the tick checks pinned tests and starts self-fixed issues first (spec fail-fix)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import NOW, FakeHost, issue, started

OPS = Path(__file__).resolve().parents[1]
PINNED_HITS = (
    "- `reviews/tests/integration/test_settings_page.py::test_get_makes_at_most_two_queries`: "
    "query cap 2\n"
    "- `reviews/tests/integration/test_settings_suggestions.py::"
    "test_settings_page_makes_at_most_two_queries`: query cap 2\n"
)


def prompt(n: int) -> str:
    return f"Use the work-queue skill for issue #{n} only."


def stamp(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, UTC).isoformat().replace("+00:00", "Z")


def self_fix(when: float) -> dict[str, Any]:
    body = "<!-- work-queue -->\n<!-- self-fix -->\n## Decisions\n\n| a | b |\n"
    return {"author": {"login": "x"}, "body": body, "createdAt": stamp(when)}


def ready(n: int, *comments: dict[str, Any], created: str = "") -> dict[str, Any]:
    item = issue(n, "agent:ready", body="## Summary\n\nx\n", created=created)
    item["comments"] = list(comments)
    return item


@dataclass
class PinHost(FakeHost):
    """FakeHost whose pinned_tests run answers with `pinned`."""

    pinned: tuple[int, str] = (0, "")
    bodies: list[str] = field(default_factory=list)

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if any(str(a).endswith("pinned_tests.py") for a in args):
            self.calls.append(args)
            self.bodies.append(Path(args[-1]).read_text())
            return self.pinned
        return super().run(args, cwd)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    return tmp_path


# AC1: the pinned-tests check before each issue build


def test_unlisted_pinned_tests_add_one_line_to_the_prompt(home: Path) -> None:
    host = PinHost(issues=[ready(7)], pinned=(1, PINNED_HITS))
    agent_tick.tick_once(host, home)
    line = (
        "Pinned tests not listed: "
        "reviews/tests/integration/test_settings_page.py::test_get_makes_at_most_two_queries, "
        "reviews/tests/integration/test_settings_suggestions.py::"
        "test_settings_page_makes_at_most_two_queries. "
        "Settle them with the self-fix step before you write code."
    )
    assert started(host) == [f"{prompt(7)}\n{line}"]


def test_the_check_runs_the_script_on_the_issue_body(home: Path) -> None:
    host = PinHost(issues=[ready(7)])
    agent_tick.tick_once(host, home)
    call = next(c for c in host.calls if any(str(a).endswith("pinned_tests.py") for a in c))
    assert str(OPS / "pinned_tests.py") in call and "--unlisted" in call
    assert host.bodies == ["## Summary\n\nx\n"]


@pytest.mark.parametrize("answer", [(0, ""), (2, "Cannot read the issue body: x")])
def test_no_unlisted_hit_adds_no_line(home: Path, answer: tuple[int, str]) -> None:
    host = PinHost(issues=[ready(7)], pinned=answer)
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(7)]


# AC2: a self-fixed issue goes first


def test_a_self_fixed_issue_starts_before_an_older_ready_issue(home: Path) -> None:
    older = ready(3, created="2026-10-01T00:00:00Z")
    fixed = ready(9, self_fix(NOW - 60), created="2026-10-20T00:00:00Z")
    host = PinHost(issues=[older, fixed])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(9)]


def test_the_oldest_self_fix_goes_first(home: Path) -> None:
    newer = ready(4, self_fix(NOW - 60), created="2026-10-01T00:00:00Z")
    older = ready(8, self_fix(NOW - 600), created="2026-10-20T00:00:00Z")
    host = PinHost(issues=[newer, older])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(8)]


def test_a_self_fix_older_than_the_last_build_start_does_not_jump(home: Path) -> None:
    done = home / "runs" / "done" / "issue-9-1"
    done.mkdir(parents=True)
    (done / "started").write_text(str(int(NOW - 30)))
    older = ready(3, created="2026-10-01T00:00:00Z")
    fixed = ready(9, self_fix(NOW - 60), created="2026-10-20T00:00:00Z")
    host = PinHost(issues=[older, fixed])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(3)]


def test_a_self_fixed_issue_still_waits_for_its_dependency(home: Path) -> None:
    blocker = issue(2, "agent:review")
    fixed = ready(9, self_fix(NOW - 60))
    fixed["body"] = "Depends on #2\n"
    older = ready(3, created="2026-10-01T00:00:00Z")
    host = PinHost(issues=[blocker, older, fixed])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(3)]


def test_a_comment_with_only_the_work_queue_marker_is_not_a_self_fix() -> None:
    plain = {"body": "<!-- work-queue -->\nRetry 1 of 3.", "createdAt": stamp(NOW)}
    assert agent_tick.self_fix_time(ready(9, plain)) is None
    assert agent_tick.self_fix_time(ready(9, self_fix(NOW))) == pytest.approx(NOW)


def test_the_issue_list_reads_comments() -> None:
    host = FakeHost()
    tick = agent_tick.Tick(host, Path("/tmp"), agent_tick.Settings(concurrency=1, ntfy_topic=""))
    agent_tick.open_issue_list(tick)
    call = host.gh_calls("issue", "list")[0]
    assert "comments" in call[call.index("--json") + 1].split(",")


# AC3: a second stop goes to the owner


def test_a_decision_stop_after_a_self_fix_is_a_decision_stop(home: Path) -> None:
    run = home / "runs" / "issue-9"
    run.mkdir(parents=True)
    (run / "started").write_text(str(int(NOW - 100)))
    stop = {
        "body": "<!-- work-queue -->\n<!-- needs-decision -->\nStill stuck.",
        "createdAt": stamp(NOW - 10),
    }
    host = FakeHost(
        issues=[issue(9, "agent:failed")],
        issue_comments={9: [self_fix(NOW - 500), stop]},
    )
    tick = agent_tick.Tick(host, home, agent_tick.Settings(concurrency=1, ntfy_topic="t"))
    assert agent_tick.needs_decision(tick, run, "9") is True
    agent_tick.decision_stop(tick, 9)
    record = agent_tick.failed_record(tick, 9)
    assert record is not None and record["kind"] == "decision"
    assert agent_tick.retry_reason(tick, issue(9, "agent:failed")) == ""
    assert host.sent == [
        f"t: {agent_tick.NAME} #9 needs your decision: https://github.com/{agent_tick.REPO}/issues/9"
    ]


# AC4: README


def test_the_readme_describes_the_check_and_the_order() -> None:
    text = (OPS / "README.md").read_text()
    assert "pinned_tests.py --unlisted" in text
    assert "<!-- self-fix -->" in text
