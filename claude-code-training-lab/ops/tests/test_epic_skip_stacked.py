"""#303: the tick never merges a pull request based on the epic branch into it (AC1, AC2, AC4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ops.tests.test_epic_branch import BRANCH, epic_pr, host_for, merges, tick


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def test_pull_request_based_on_the_epic_branch_is_not_merged_into_it(home: Path) -> None:
    stacked = epic_pr(number=21, closes=6, oid="bbb2222") | {"baseRefName": BRANCH}
    host = host_for(epic_pr(), stacked, branches={BRANCH})
    tick(host, home)
    merged = [m[-1] for m in merges(host)]
    assert "abc1234def" in merged
    assert "bbb2222" not in merged


def test_log_line_counts_only_pull_requests_based_on_main(home: Path) -> None:
    stacked = epic_pr(number=21, closes=6, oid="bbb2222") | {"baseRefName": BRANCH}
    host = host_for(epic_pr(), stacked, branches={BRANCH})
    log = tick(host, home)
    assert [line for line in log if line.startswith("epic #")] == [
        f"epic #236: branch {BRANCH}, 1 pull requests in it"
    ]
