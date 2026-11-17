"""#587: the tick heals a failed issue, up to 3 times (spec depends-heal). Run: pytest ops"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick, epic_pull_request
from ops.agent_tick import MARKER, REPO
from ops.tests.test_agent_tick import NOW, add_run, issue, started
from ops.tests.test_epic_pull_request import host_for, tick, two_merged
from ops.tests.test_tick_hardening import GitHost

OLD = "1111111aaaaaaa"
NEW = "2222222bbbbbbb"
FILES = "## Files likely touched\n\n- `ops/x.py`\n"
OTHER = "## Files likely touched\n\n- `ops/y.py`\n"
BEGAN = int(NOW) - 600
PLUGIN = Path(__file__).resolve().parents[3] / "plugins" / "agent-flow"
SKILL = PLUGIN / "skills" / "work-queue" / "SKILL.md"
URL = "https://github.com/o/r/issues/5#issuecomment-88"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def one_slot(home: Path) -> None:
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")


def on_main(head: str) -> dict[str, tuple[int, str]]:
    return {"branch --show-current": (0, "main\n"), "rev-parse origin/main": (0, head + "\n")}


def stamp(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, UTC).isoformat().replace("+00:00", "Z")


def heal_prompt(n: int) -> str:
    return f"Use the work-queue skill for issue #{n} only: heal."


def prompt(n: int) -> str:
    return f"Use the work-queue skill for issue #{n} only."


def write(home: Path, number: int = 1, **fields: Any) -> None:
    folder = home / "failed"
    folder.mkdir(exist_ok=True)
    data = {"main": OLD, "kind": "decision", "retries": 0, "outcome": ""} | fields
    (folder / str(number)).write_text(json.dumps(data))


def record(home: Path, number: int = 1) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((home / "failed" / str(number)).read_text())
    return data


def heals(home: Path, number: int = 1) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((home / "heals" / str(number)).read_text())
    return data


def write_heals(home: Path, count: int, told: bool = False, number: int = 1) -> None:
    (home / "heals").mkdir(exist_ok=True)
    (home / "heals" / str(number)).write_text(json.dumps({"count": count, "told": told}))


def heal_comment(when: float, owner: bool = False, url: str = URL) -> dict[str, Any]:
    third = "<!-- needs-owner -->\n" if owner else ""
    body = f"{MARKER}\n<!-- heal -->\n{third}## Decisions\n\n| a | b | c |\n"
    return {"author": {"login": "x"}, "body": body, "createdAt": stamp(when), "url": url}


def failed(n: int = 1, body: str = FILES, *comments: dict[str, Any]) -> dict[str, Any]:
    item = issue(n, "agent:failed", body=body)
    item["comments"] = list(comments)
    return item


def ready(
    n: int, body: str = OTHER, *comments: dict[str, Any], created: str = ""
) -> dict[str, Any]:
    item = issue(n, "agent:ready", body=body, created=created)
    item["comments"] = list(comments)
    return item


def heal_run(home: Path, exit_text: str | None, log: str = "") -> Path:
    run = add_run(home, "issue-1", 77, exit_text=exit_text, log=log)
    (run / "started").write_text(str(BEGAN))
    (run / "heal").touch()
    return run


def link(n: int = 1) -> str:
    return f"https://github.com/{REPO}/issues/{n}"


# M11: AC1, AC3, AC4 — the heal run goes before an older ready issue


def test_a_failed_decision_is_healed_before_an_older_ready_issue(home: Path) -> None:
    one_slot(home)
    write(home)
    host = GitHost(issues=[failed(), ready(5, created="2026-09-01T00:00:00Z")], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [heal_prompt(1)]
    assert heals(home) == {"count": 1, "told": False}
    edit = ["gh", "issue", "edit", "1", "--add-label", "agent:running"]
    edits = [c for c in host.calls if c[:6] == edit]
    assert edits and edits[0][6:8] == ["--remove-label", "agent:failed"]
    assert "rr-test: ReviewRadar healing #1 (1 of 3)" in host.sent
    assert (home / "runs" / "issue-1" / "heal").exists()


def test_heal_runs_go_oldest_record_first(home: Path) -> None:
    one_slot(home)
    write(home, 1)
    write(home, 2)
    import os

    os.utime(home / "failed" / "1", (NOW - 10, NOW - 10))
    os.utime(home / "failed" / "2", (NOW - 100, NOW - 100))
    host = GitHost(issues=[failed(1), failed(2, OTHER)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [heal_prompt(2)]


def test_a_heal_run_starts_detached_at_main_and_archives_no_branch(home: Path) -> None:
    write(home)
    (home / "worktrees" / "issue-1").mkdir(parents=True)
    git = on_main(OLD) | {"branch --list": (0, "task/1-old\n")}
    host = GitHost(issues=[failed()], git=git)
    agent_tick.tick_once(host, home)
    assert started(host) == [heal_prompt(1)]
    assert host.git_calls("worktree move")
    assert host.git_calls("branch -m") == []
    assert host.git_calls("worktree add --detach")[0][-1] == "origin/main"
    assert (home / "runs" / "issue-1" / "allowed-edits").read_text() == ""


def test_a_heal_run_needs_the_owners_ready_label(home: Path) -> None:
    write(home)
    host = GitHost(issues=[failed()], git=on_main(OLD), labeller={1: "stranger"})
    agent_tick.tick_once(host, home)
    assert started(host) == []
    assert not (home / "heals" / "1").exists()


# M12: AC2 — a heal ignores Depends on and the file-overlap guard


def test_a_heal_starts_despite_a_shared_file_and_an_open_dependency(home: Path) -> None:
    write(home, kind="stopped")
    blocked = failed(1, FILES + "\nDepends on #3\n")
    host = GitHost(
        issues=[blocked, issue(2, "agent:running", body=FILES), issue(3)], git=on_main(OLD)
    )
    add_run(home, "issue-2", 55)
    host.alive_pids.add(55)
    agent_tick.tick_once(host, home)
    assert started(host) == [heal_prompt(1)]


def test_a_held_issue_with_a_retry_reason_stays_held(home: Path) -> None:
    write(home, kind="transient", retries=1)
    blocked = failed(1, FILES + "\nDepends on #3\n")
    host = GitHost(issues=[blocked, issue(3)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == []


# M13: AC1 — retries first, a heal after the third; no record waits


def test_a_transient_failure_with_one_retry_is_retried_not_healed(home: Path) -> None:
    write(home, kind="transient", retries=1, outcome="stopped after 45 minutes")
    host = GitHost(issues=[failed()], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]
    assert not (home / "heals" / "1").exists()


def test_a_transient_failure_after_three_retries_is_healed(home: Path) -> None:
    write(home, kind="transient", retries=3)
    host = GitHost(issues=[failed()], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [heal_prompt(1)]


def test_a_failed_issue_without_a_record_gets_one_and_waits(home: Path) -> None:
    host = GitHost(issues=[failed()], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "stopped"
    assert started(host) == []


# M14: AC9, AC10, AC11 — the work-queue skill


def section(text: str, heading: str) -> str:
    start = text.index(f"\n{heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def test_the_skill_has_a_heal_section_in_place() -> None:
    text = SKILL.read_text()
    assert text.index("\n## Epic review\n") < text.index("\n## Heal\n")
    assert text.index("\n## Heal\n") < text.index("\n## 2. One new issue\n")
    target = section(text, "## One target (from the tick)")
    assert "Use the work-queue skill for issue #<n> only: heal." in target
    assert "`## Heal`" in target
    assert "ADR-034" not in text


def test_the_heal_section_says_what_it_reads_does_and_never_does() -> None:
    heal = section(SKILL.read_text(), "## Heal")
    for words in (
        "Use the work-queue skill for issue #<n> only: heal.",
        "section 2 is not run",
        "`Decisions` and `Design`",
        "other issues of its epic",
        "newest stop comment",
        "narrowest reading",
        "recommended option in the spec",
        "gh issue edit <n> --body-file",
        "<!-- heal -->",
        "## Decisions",
        "agent:ready",
        "Pinned tests not listed",
        "commits nothing",
        "delete files or data",
        "migration",
        "security, secrets, permissions or sign-in",
        "turns a guard off",
        "`.claude/`",
        "weaken a test",
        "query count that grows with the data",
        "<!-- needs-owner -->",
        "agent:failed",
    ):
        assert words in heal, words


def test_step_four_points_to_heal() -> None:
    step = section(SKILL.read_text(), "## 2. One new issue")
    assert "never retries such a stop" not in step
    assert "`## Heal`" in step and "3 times" in step


# M15: AC2, AC6 — a heal that hands the issue to the owner


def test_a_needs_owner_heal_sends_one_message_and_is_not_healed_again(home: Path) -> None:
    write(home, kind="stopped")
    write_heals(home, 1)
    heal_run(home, "0")
    asked = heal_comment(NOW - 300, owner=True)
    host = GitHost(issues=[failed(1, FILES, asked)], issue_comments={1: [asked]}, git=on_main(NEW))
    agent_tick.tick_once(host, home)
    message = f"rr-test: ReviewRadar #1 cannot be healed, needs you: {link()}"
    assert [m for m in host.sent if "#1" in m] == [message]
    assert record(home)["kind"] == "decision"
    host.clock += 600
    agent_tick.tick_once(host, home)
    assert started(host) == []
    assert [m for m in host.sent if "#1" in m] == [message]


def test_an_owner_restart_after_a_needs_owner_heal_makes_it_count_no_more(home: Path) -> None:
    write(home)
    write_heals(home, 1)
    done = home / "runs" / "done" / "issue-1-1"
    done.mkdir(parents=True)
    (done / "started").write_text(str(int(NOW - 60)))
    host = GitHost(issues=[failed(1, FILES, heal_comment(NOW - 300, owner=True))])
    agent_tick.tick_once(host, home)
    assert started(host) == [heal_prompt(1)]


# M16: AC5 — after the third heal


def test_after_three_heals_the_owner_is_told_once_and_others_go_on(home: Path) -> None:
    write(home)
    write_heals(home, 3)
    host = GitHost(issues=[failed(), ready(2)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    message = f"rr-test: ReviewRadar #1 failed after 3 heals, needs you: {link()}"
    assert host.sent.count(message) == 1
    assert started(host) == [prompt(2)]
    assert heals(home) == {"count": 3, "told": True}
    host.clock += 600
    agent_tick.tick_once(host, home)
    assert host.sent.count(message) == 1
    assert started(host) == [prompt(2)]


def test_the_owners_ready_label_resets_told(home: Path) -> None:
    write_heals(home, 3, told=True)
    host = GitHost(issues=[ready(1)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert heals(home) == {"count": 3, "told": False}


def test_a_ready_label_of_another_login_does_not_reset_told(home: Path) -> None:
    write_heals(home, 3, told=True)
    host = GitHost(issues=[ready(1)], git=on_main(OLD), labeller={1: "stranger"})
    agent_tick.tick_once(host, home)
    assert heals(home) == {"count": 3, "told": True}


# AC4: a heal run that crashes, or hits the plan limit


def test_a_crashed_heal_keeps_the_kind_and_sends_the_failed_message(home: Path) -> None:
    write(home, kind="decision", retries=2)
    write_heals(home, 1)
    heal_run(home, "timeout")
    host = GitHost(issues=[issue(1, "agent:running")], git=on_main(NEW))
    agent_tick.tick_once(host, home)
    assert record(home) | {"main": ""} == {
        "main": "",
        "kind": "decision",
        "retries": 2,
        "outcome": "stopped after 45 minutes",
    }
    message = "rr-test: ReviewRadar build for issue #1 failed: stopped after 45 minutes"
    assert [m for m in host.sent if "#1" in m] == [message]
    edit = ["gh", "issue", "edit", "1", "--add-label", "agent:failed"]
    assert any(c[:6] == edit for c in host.calls)
    assert heals(home)["count"] == 1


def test_a_heal_stopped_by_the_plan_limit_goes_back_to_failed(home: Path) -> None:
    write(home, kind="stopped", retries=1)
    before = (home / "failed" / "1").read_text()
    write_heals(home, 2)
    heal_run(home, "1", log="You've hit your 5-hour limit")
    host = GitHost(issues=[issue(1, "agent:running")], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    edit = [
        "gh", "issue", "edit", "1", "--add-label", "agent:failed", "--remove-label",
        "agent:running", "--repo", REPO,
    ]  # fmt: skip
    assert edit in host.calls
    assert not any("agent:ready" in c for c in host.calls if c[:3] == ["gh", "issue", "edit"])
    assert (home / "failed" / "1").read_text() == before
    assert heals(home)["count"] == 1
    assert (home / "paused-until").exists()


def test_a_heal_that_ends_with_no_agent_label_is_a_failed_heal(home: Path) -> None:
    write(home, kind="decision", retries=1)
    write_heals(home, 1)
    heal_run(home, "0")
    host = GitHost(issues=[issue(1)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    edit = ["gh", "issue", "edit", "1", "--add-label", "agent:failed"]
    assert any(c[:6] == edit for c in host.calls)
    assert record(home)["kind"] == "decision"
    assert [m for m in host.sent if "#1" in m] == [
        "rr-test: ReviewRadar build for issue #1 failed: ended without a pull request"
    ]


def test_a_heal_that_ends_ready_archives_the_failure_record(home: Path) -> None:
    write(home, retries=2)
    write_heals(home, 1)
    heal_run(home, "0")
    host = GitHost(issues=[ready(1, FILES)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert not (home / "failed" / "1").exists()
    assert heals(home)["count"] == 1


# AC7: the changed messages


def test_a_decision_stop_at_three_heals_sends_the_heal_message(home: Path) -> None:
    write_heals(home, 3)
    host = GitHost(issues=[issue(1, "agent:failed")], git=on_main(OLD))
    t = agent_tick.Tick(host, home, agent_tick.Settings(concurrency=1, ntfy_topic="t"))
    agent_tick.decision_stop(t, 1)
    agent_tick.decision_stop(t, 1)
    assert host.sent == [f"t: {agent_tick.NAME} #1 failed after 3 heals, needs you: {link()}"]
    assert heals(home)["told"] is True


def test_a_decision_stop_with_a_counting_needs_owner_heal_sends_the_owner_message(
    home: Path,
) -> None:
    asked = heal_comment(NOW - 60, owner=True)
    host = GitHost(issues=[failed(1, FILES, asked)], issue_comments={1: [asked]})
    t = agent_tick.Tick(host, home, agent_tick.Settings(concurrency=1, ntfy_topic="t"))
    agent_tick.decision_stop(t, 1)
    assert host.sent == [f"t: {agent_tick.NAME} #1 cannot be healed, needs you: {link()}"]


def test_a_decision_stop_after_the_third_retry_sends_one_message(home: Path) -> None:
    write(home, kind="transient", retries=3)
    host = GitHost(issues=[issue(1, "agent:failed")], git=on_main(OLD))
    t = agent_tick.Tick(host, home, agent_tick.Settings(concurrency=1, ntfy_topic="t"))
    agent_tick.decision_stop(t, 1)
    assert host.sent == [
        f"t: {agent_tick.NAME} #1 stopped for a decision; the loop heals it next: {link()}"
    ]


def test_unreadable_comments_after_a_heal_keep_the_run_for_the_next_tick(home: Path) -> None:
    write(home, kind="stopped")
    heal_run(home, "0")
    host = GitHost(issues=[failed()], git=on_main(OLD), fail="view 1 --json comments")
    with pytest.raises(RuntimeError, match="view 1 --json comments"):
        agent_tick.tick_once(host, home)
    assert (home / "runs" / "issue-1").exists()
    assert record(home)["kind"] == "stopped"


# M17: AC8, AC12 — a healed issue goes first, and the epic pull request lists the heal


def test_a_healed_ready_issue_starts_before_an_older_ready_issue(home: Path) -> None:
    one_slot(home)
    older = ready(3, created="2026-09-01T00:00:00Z")
    healed = ready(9, FILES, heal_comment(NOW - 60), created="2026-10-20T00:00:00Z")
    host = GitHost(issues=[older, healed], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(9)]


def test_the_first_build_after_a_heal_archives_the_old_branches(home: Path) -> None:
    git = on_main(OLD) | {"branch --list": (0, "task/9-old\n")}
    healed = ready(9, FILES, heal_comment(NOW - 60))
    host = GitHost(issues=[healed], git=git)
    agent_tick.tick_once(host, home)
    renames = host.git_calls("branch -m task/9-old")
    assert renames and renames[0][-1].startswith("archive/task/9-old-")


def test_the_epic_body_lists_a_heal_under_self_decided_fixes(home: Path) -> None:
    owner = heal_comment(NOW, owner=True, url=URL.replace("88", "89"))
    host = host_for(*two_merged(), issue_comments={5: [heal_comment(NOW), owner]})
    tick(host, home)
    assert f"## Self-decided fixes\n\n- #5: {URL}\n" in host.bodies[0]
    assert URL.replace("88", "89") not in host.bodies[0]


def test_a_needs_owner_heal_is_not_a_self_decided_fix() -> None:
    owner = heal_comment(NOW, owner=True)
    assert epic_pull_request.self_fix_urls([heal_comment(NOW), owner]) == [URL]


# AC8: the heal count leaves when the issue closes, never on a restart


def test_the_heal_count_is_archived_when_the_issue_closes(home: Path) -> None:
    write_heals(home, 2)
    host = GitHost(issues=[], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert not (home / "heals" / "1").exists()
    assert any(p.name.startswith("heals-1-") for p in (home / "archive").iterdir())


def test_the_heal_count_stays_when_the_issue_is_restarted(home: Path) -> None:
    write_heals(home, 2)
    host = GitHost(issues=[ready(1)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert heals(home)["count"] == 2


# AC13: README and plugin version


def test_the_readme_describes_heal_runs() -> None:
    text = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    for words in ("heal run", "healing #<n> (<k> of 3)", "failed after 3 heals, needs you"):
        assert words in text, words
    assert "cannot be healed, needs you" in text
    assert "stopped for a decision; the loop heals it next" in text
