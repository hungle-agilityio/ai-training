"""#586: a build that waits for its base task ends normally. Run: pytest ops"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import add_run, issue, started
from ops.tests.test_tick_waiting import WaitingHost, depends

SKILL = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "agent-flow"
    / "skills"
    / "work-queue"
    / "SKILL.md"
)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def claim_step() -> str:
    text = SKILL.read_text()
    start = text.index("2. **Claim.**")
    return text[start : text.index("3. **Analyse.**", start)]


def issue_bullet() -> str:
    text = SKILL.read_text()
    section = text[text.index("## One target (from the tick)") :]
    start = section.index("- **Issue #N:**")
    end = section.find("\n- ", start + 1)
    return section[start:] if end == -1 else section[start:end]


# AC1: the skill text


@pytest.mark.parametrize(
    "needle",
    [
        "**Dependencies.**",
        "<!-- waiting -->",
        "agent:in-epic",
        "agent:ready",
        "without `agent:failed`",
    ],
)
def test_claim_step_holds_the_dependencies_check(needle: str) -> None:
    assert needle in claim_step()


@pytest.mark.parametrize("needle", ["**Dependencies.**", "step 2"])
def test_issue_target_bullet_runs_the_dependencies_check_first(needle: str) -> None:
    assert needle in issue_bullet()


def test_dependencies_check_comes_before_the_branch() -> None:
    bullet = issue_bullet()
    claim = claim_step()
    assert bullet.index("**Dependencies.**") < bullet.index("git switch -c")
    assert claim.index("After the **Dependencies.** check") < claim.index("branch `<kind>/<id>")


# AC2: the tick treats the waiting end as a normal end


def test_run_that_released_its_issue_to_ready_ends_normally(home: Path) -> None:
    add_run(home, "issue-5", 77, exit_text="0")
    host = WaitingHost(issues=[issue(5, "agent:ready", body=depends(4)), issue(4)])
    log = agent_tick.tick_once(host, home)
    added = [
        c[c.index("--add-label") + 1] for c in host.gh_calls("issue", "edit") if "--add-label" in c
    ]
    assert "issue-5: ended normally" in log
    assert not any("agent:failed" in label for label in added)
    assert not (home / "failed" / "5").exists()
    assert not any("failed" in m or "needs your decision" in m for m in host.sent)
    assert started(host) == []
