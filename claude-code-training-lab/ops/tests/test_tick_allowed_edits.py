"""#387: the tick passes the issue's files to the build and shows guard files (ADR-023)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick, bootstrap, epic_pull_request
from ops.tests.test_agent_tick import FakeHost, issue, pull, started
from ops.tests.test_build_artifact_tool import RESULT, WITH, Child, Fake
from ops.tests.test_tick_hardening import GitHost

OPS = Path(__file__).resolve().parents[1]
PREFIX = agent_tick.LAB_PREFIX
LINK = "https://claude.ai/artifact/abc"
BODY = (
    "## Summary\n\nx\n\n## Files likely touched\n\n"
    f"- `{PREFIX}reviews/views.py`\n"
    f"- `{PREFIX}.claude/rules/git.md`\n"
    "- `../plugins/agent-flow/hooks/before-edit-check.py`\n"
    f"- `{PREFIX}reviews/tests/unit/test_new.py` (NEW)\n\n"
    "## Existing tests that change\n\n"
    f"- `{PREFIX}reviews/tests/unit/test_old.py::test_a`: x.\n"
    f"- `{PREFIX}reviews/tests/unit/test_old.py::test_b`: x.\n\n"
    "## How to check it when built\n\n1. x\n"
)
LISTED = (
    "../plugins/agent-flow/hooks/before-edit-check.py\n"
    ".claude/rules/git.md\n"
    "reviews/tests/unit/test_new.py\n"
    "reviews/tests/unit/test_old.py\n"
    "reviews/views.py\n"
)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


# AC1: the allowed-edits file and FLOW_ALLOWED_EDITS


def test_the_list_holds_every_listed_path_once_without_prefix_or_test_name() -> None:
    assert agent_tick.allowed_edits_of(BODY) == tuple(LISTED.splitlines())


def test_a_body_without_listed_paths_gives_nothing() -> None:
    assert agent_tick.allowed_edits_of("## Summary\n\nx\n") == ()


def test_an_issue_build_writes_the_allowed_edits_file(home: Path) -> None:
    host = GitHost(issues=[issue(290, "agent:ready", body=BODY)])
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "issue-290" / "allowed-edits").read_text() == LISTED


def test_an_issue_without_listed_paths_writes_an_empty_file(home: Path) -> None:
    host = GitHost(issues=[issue(291, "agent:ready", body="## Summary\n\nx\n")])
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "issue-291" / "allowed-edits").read_text() == ""


def test_a_pull_request_round_uses_the_list_of_its_issue(home: Path) -> None:
    host = GitHost(prs=[pull(300, closes=290)], issues=[issue(290, "agent:review", body=BODY)])
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "pr-300" / "allowed-edits").read_text() == LISTED


def test_the_build_gets_the_variable_from_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = tmp_path / "runs" / "issue-290"
    run.mkdir(parents=True)
    (run / "allowed-edits").write_text(LISTED)
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_start(run, tmp_path, "p", 1, 10**12)
    assert fake.starts[0][1]["env"]["FLOW_ALLOWED_EDITS"] == LISTED.strip()


def test_an_empty_file_gives_an_empty_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLOW_ALLOWED_EDITS", ".claude/settings.json")
    run = tmp_path / "runs" / "issue-291"
    run.mkdir(parents=True)
    (run / "allowed-edits").write_text("")
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_start(run, tmp_path, "p", 1, 10**12)
    assert fake.starts[0][1]["env"]["FLOW_ALLOWED_EDITS"] == ""


def test_without_the_file_a_leaked_value_is_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLOW_ALLOWED_EDITS", ".claude/settings.json")
    run = tmp_path / "runs" / "issue-292"
    run.mkdir(parents=True)
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_start(run, tmp_path, "p", 1, 10**12)
    assert "FLOW_ALLOWED_EDITS" not in fake.starts[0][1]["env"]


# AC2: agent:manual and agent:needs-permission are not read


def test_manual_is_not_a_skip_label() -> None:
    assert agent_tick.SKIP_LABELS == {"agent:running", "agent:review", "agent:failed"}


@pytest.mark.parametrize("label", ["agent:manual", "agent:needs-permission", "agent:other"])
def test_a_ready_issue_starts_whatever_other_agent_label_it_has(home: Path, label: str) -> None:
    host = GitHost(issues=[issue(7, "agent:ready", label, body="## Summary\n\nx\n")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #7 only."]


def test_the_tick_names_neither_old_label() -> None:
    for name in ("agent_tick.py", "epic_pull_request.py", "README.md"):
        text = (OPS / name).read_text()
        assert "agent:manual" not in text and "agent:needs-permission" not in text


# AC3: the Guard files changed section


DIFF = (
    "M\tclaude-code-training-lab/reviews/views.py\n"
    "M\tclaude-code-training-lab/.claude/rules/git.md\n"
    "A\t.github/workflows/new.yml\n"
    "M\tplugins/agent-flow/hooks/before-edit-check.py\n"
    "D\tclaude-code-training-lab/pyproject.toml\n"
    "M\tclaude-code-training-lab/reviews/tests/unit/test_old.py\n"
    "A\tclaude-code-training-lab/reviews/tests/unit/test_new.py\n"
    "R087\tclaude-code-training-lab/a.json\tclaude-code-training-lab/.mcp.json\n"
    "M\t.claude-plugin/marketplace.json\n"
    "M\tclaude-code-training-lab/ops/plugins_note.md\n"
)
GUARDED = [
    "claude-code-training-lab/.claude/rules/git.md",
    ".github/workflows/new.yml",
    "plugins/agent-flow/hooks/before-edit-check.py",
    "claude-code-training-lab/pyproject.toml",
    "claude-code-training-lab/reviews/tests/unit/test_old.py",
    "claude-code-training-lab/.mcp.json",
    ".claude-plugin/marketplace.json",
]


def test_guard_paths_follow_the_edit_hook() -> None:
    assert epic_pull_request.guard_paths(DIFF, ("reviews/tests",)) == GUARDED


def test_the_section_stands_above_closes() -> None:
    body = f"{agent_tick.MARKER}\nWhat.\n\nCloses #9\n"
    done = epic_pull_request.with_guard_section(body, ["a/.claude/x.md"])
    assert done == (
        f"{agent_tick.MARKER}\nWhat.\n\n## Guard files changed\n\n- `a/.claude/x.md`\n\nCloses #9\n"
    )


def test_an_empty_list_says_none_and_an_old_section_is_replaced() -> None:
    body = "What.\n\n## Guard files changed\n\n- `old.toml`\n\nCloses #9\n"
    done = epic_pull_request.with_guard_section(body, [])
    assert done == "What.\n\n## Guard files changed\n\nNone.\n\nCloses #9\n"


def test_a_body_without_closes_gets_the_section_at_the_end() -> None:
    done = epic_pull_request.with_guard_section("What.\n", ["x/.github/a.yml"])
    assert done == "What.\n\n## Guard files changed\n\n- `x/.github/a.yml`\n"


@dataclass
class DiffHost(FakeHost):
    """FakeHost whose `git diff` answers with `diff` and keeps the edited bodies."""

    diff: tuple[int, str] = (0, "")
    bodies: list[str] = field(default_factory=list)

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[0] == "git" and "diff" in args:
            self.calls.append(args)
            return self.diff
        if args[:3] == ["gh", "pr", "edit"] and "--body-file" in args:
            self.calls.append(args)
            self.bodies.append(Path(args[args.index("--body-file") + 1]).read_text())
            return 0, ""
        return super().run(args, cwd)


def green(number: int) -> dict[str, Any]:
    pr = pull(number, closes=number + 100)
    pr["body"] = f"{agent_tick.MARKER}\nVerify report: {LINK}\nCloses #{number + 100}"
    return pr


def make_tick(tmp_path: Path, host: FakeHost) -> agent_tick.Tick:
    return agent_tick.Tick(host, tmp_path, agent_tick.Settings(concurrency=1, ntfy_topic="t"))


def test_first_ready_label_adds_the_section_and_a_flagged_message(tmp_path: Path) -> None:
    host = DiffHost(diff=(0, DIFF))
    prs = [green(5)]
    agent_tick.mark_green_ready(make_tick(tmp_path, host), prs, {})
    assert len(host.bodies) == 1
    body = host.bodies[0]
    assert "\n## Guard files changed\n\n- `claude-code-training-lab/.claude/rules/git.md`\n" in body
    assert body.index("## Guard files changed") < body.index("Closes #105")
    assert prs[0]["body"] == body
    diff = next(c for c in host.calls if c[0] == "git" and "diff" in c)
    assert "origin/main...origin/task/105-x" in diff
    assert len(host.sent) == 1
    assert host.sent[0].startswith("t: ")
    assert "PR #5 ready for review for #105" in host.sent[0]
    assert host.sent[0].endswith(" (changes guard files)")


def test_no_guard_file_says_none_and_sends_nothing_new(tmp_path: Path) -> None:
    host = DiffHost(diff=(0, "M\tclaude-code-training-lab/reviews/views.py\n"))
    agent_tick.mark_green_ready(make_tick(tmp_path, host), [green(5)], {})
    assert "## Guard files changed\n\nNone.\n" in host.bodies[0]
    assert host.sent == []


def test_a_diff_that_cannot_be_read_waits_for_the_next_tick(tmp_path: Path) -> None:
    host = DiffHost(diff=(1, "fatal: bad revision"))
    tick = make_tick(tmp_path, host)
    prs = [green(5)]
    agent_tick.mark_green_ready(tick, prs, {})
    assert host.bodies == []
    assert agent_tick.names(prs[0]) == set()
    assert any("guard files not read" in line for line in tick.log)


def test_a_stacked_pull_request_is_compared_with_its_base(tmp_path: Path) -> None:
    host = DiffHost(diff=(0, ""))
    pr = green(5) | {"baseRefName": "task/104-y"}
    agent_tick.mark_green_ready(make_tick(tmp_path, host), [pr], {})
    diff = next(c for c in host.calls if c[0] == "git" and "diff" in c)
    assert "origin/task/104-y...origin/task/105-x" in diff


def test_a_pull_request_message_is_flagged_when_its_body_lists_guard_files() -> None:
    pr = green(5) | {"body": "x\n\n## Guard files changed\n\n- `a/.claude/b.md`\n\nCloses #105"}
    assert agent_tick.pr_message(pr, "updated").endswith(" (changes guard files)")
    none = green(5) | {"body": "x\n\n## Guard files changed\n\nNone.\n\nCloses #105"}
    assert not agent_tick.pr_message(none, "updated").endswith(" (changes guard files)")


def test_the_epic_body_has_the_section_above_closes() -> None:
    body = epic_pull_request.body_for("m", 9, "epic/9-x", [5], [], [], ["a/.github/b.yml"])
    assert "## Guard files changed\n\n- `a/.github/b.yml`\n\nCloses #5\nCloses #9\n" in body


# AC4: bootstrap


def test_the_manifest_no_longer_creates_the_old_labels() -> None:
    manifest = tomllib.loads((OPS / "bootstrap_manifest.toml").read_text())
    names = {label["name"] for label in manifest["label"]}
    assert "agent:ready" in names
    assert not names & {"agent:manual", "agent:needs-permission"}


def test_bootstrap_steps_no_longer_warn_about_needs_permission(tmp_path: Path) -> None:
    params = bootstrap.Params(
        target=tmp_path, repo="o/r", owner="o", app_dir=".", name="Shop", slug="shop",
        ntfy_topic="t", dry_run=True, labels=False,
    )  # fmt: skip
    assert not any("needs-permission" in step for step in bootstrap.steps(params))
