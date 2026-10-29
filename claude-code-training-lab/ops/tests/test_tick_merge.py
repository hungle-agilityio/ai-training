"""The tick merges on the owner's approval and runs open change requests. Run: pytest ops/tests"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, OWNER
from ops.tests.test_agent_tick import FakeHost, add_run, started

OPENED = "2026-10-20T09:00:00Z"
LOOP_COMMIT = "2026-10-20T10:00:00Z"
URL = "https://github.com/hungle-agilityio/ai-training/pull/20"


def remark(cid: int, body: str, when: str = "2026-10-21T00:00:00Z", login: str = OWNER,
           marks: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "id": f"IC_{cid}", "author": {"login": login}, "body": body, "createdAt": when,
        "url": f"{URL}#issuecomment-{cid}",
        "reactionGroups": [{"content": m.upper(), "users": {"totalCount": 1}} for m in marks],
    }


def inline(cid: int, body: str, when: str = "2026-10-21T00:00:00Z", login: str = OWNER,
           marks: tuple[str, ...] = ()) -> dict[str, Any]:
    return {"id": cid, "user": {"login": login}, "body": body, "created_at": when,
            "reactions": {m: 1 for m in marks}}


def loop_pr(*comments: dict[str, Any], labels: tuple[str, ...] = ("pr:ready-for-review",),
            checks: list[dict[str, Any]] | None = None, state: str = "CLEAN",
            commits: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "number": 20, "state": "OPEN", "body": f"{MARKER}\nCloses #5",
        "labels": [{"name": name} for name in labels], "headRefName": "task/5-x",
        "createdAt": OPENED, "isDraft": False, "mergeStateStatus": state,
        "headRefOid": "abc1234def",
        "commits": commits or [{"committedDate": LOOP_COMMIT, "messageHeadline": "Do the task",
                                "oid": "abc1234def"}],
        "comments": list(comments),
        "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}]
        if checks is None else checks,
    }


@dataclass
class ReviewHost(FakeHost):
    """FakeHost with line comments, reactions, merges and branch updates."""

    inline_comments: list[dict[str, Any]] = field(default_factory=list)
    reactions: dict[int, list[dict[str, Any]]] = field(default_factory=dict)
    update: tuple[int, str] = (0, "")
    merge: tuple[int, str] = (0, "")
    posted: list[tuple[int, str]] = field(default_factory=list)

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[0] == "git":
            self.calls.append(args)
            if "--show-current" in args:
                return 0, "main\n"
            return (0, "fff0001\n") if "rev-parse" in args else (0, "")
        if args[:2] == ["gh", "api"]:
            self.calls.append(args)
            path = next(a for a in args[2:] if a.startswith("repos/"))
            cid = int(path.split("/")[-2]) if path.endswith("/reactions") else 0
            if "POST" in args:
                content = args[-1].split("=", 1)[1]
                self.posted.append((cid, content))
                self.reactions.setdefault(cid, []).append(
                    {"user": {"login": OWNER}, "content": content})
                for pr in self.prs:
                    for c in pr["comments"]:
                        if c["url"].endswith(f"-{cid}"):
                            c["reactionGroups"].append(
                                {"content": content.upper(), "users": {"totalCount": 1}})
                return 0, "{}"
            if path.endswith("/reactions"):
                return 0, json.dumps(self.reactions.get(cid, []))
            return 0, json.dumps(self.inline_comments)
        if args[1:3] == ["pr", "update-branch"]:
            self.calls.append(args)
            return self.update
        if args[1:3] == ["pr", "merge"]:
            self.calls.append(args)
            return self.merge
        return super().run(args, cwd)

    def merged(self) -> bool:
        return bool(self.gh_calls("pr", "merge"))


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


PR_RUN = "Use the work-queue skill for pull request #20 only."


# AC1, AC2, AC5: approval merges


@pytest.mark.parametrize("word", ["LGTM!", "/merge", "Looks good.", "duyệt", " ship it ", "OK"])
def test_approval_word_merges_and_marks_it(home: Path, word: str) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, word))])
    agent_tick.tick_once(host, home)
    assert ["gh", "pr", "merge", "20", "--merge", "--delete-branch", "--match-head-commit",
            "abc1234def", "--repo", agent_tick.REPO] in host.calls
    assert (101, "rocket") in host.posted
    assert "rr-test: ReviewRadar PR #20 merged (#5); main is now fff0001" in host.sent


def test_lgtm_with_more_words_is_a_change_request(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm but rename X"))])
    agent_tick.tick_once(host, home)
    assert not host.merged()
    assert started(host) == [PR_RUN]


def test_approval_older_than_a_loop_commit_does_not_merge(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm", when="2026-10-20T09:30:00Z"))])
    agent_tick.tick_once(host, home)
    assert not host.merged()


def test_approval_older_only_than_an_update_from_main_merges(home: Path) -> None:
    commits = [
        {"committedDate": LOOP_COMMIT, "messageHeadline": "Do the task"},
        {"committedDate": "2026-10-22T00:00:00Z",
         "messageHeadline": "Merge branch 'main' into task/5-x"},
    ]
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), commits=commits)])
    agent_tick.tick_once(host, home)
    assert host.merged()


def test_an_approval_with_a_mark_is_not_read_again(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm", marks=("confused",)))],
                      reactions={101: [{"user": {"login": OWNER}, "content": "confused"}]})
    agent_tick.tick_once(host, home)
    assert not host.merged()


# AC3, AC4: behind, conflict, dirty, red, running


def test_behind_main_updates_the_branch_and_does_not_merge(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), state="BEHIND")])
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "update-branch") and not host.merged()
    assert host.posted == []


def test_conflict_on_update_posts_the_redo_and_marks_the_approval(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), state="BEHIND")],
                      update=(1, "merge conflict between base and head"))
    agent_tick.tick_once(host, home)
    comment = host.gh_calls("pr", "comment")[0]
    assert comment[comment.index("--body") + 1] == agent_tick.REDO_CONFLICT
    assert MARKER not in " ".join(comment)
    assert (101, "confused") in host.posted and not host.merged()


def test_dirty_is_not_merged_and_said_once(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), state="DIRTY")])
    agent_tick.tick_once(host, home)
    host.prs[0]["comments"].append(remark(102, "lgtm", when="2026-10-23T00:00:00Z"))
    agent_tick.tick_once(host, home)
    assert [m for m in host.sent if "not merged" in m] == [
        "rr-test: ReviewRadar PR #20 not merged: merge state is DIRTY"]
    assert (101, "confused") in host.posted and (102, "confused") in host.posted


def test_red_check_is_not_merged(home: Path) -> None:
    red = [{"status": "COMPLETED", "conclusion": "FAILURE"}]
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), checks=red)])
    agent_tick.tick_once(host, home)
    assert not host.merged()
    assert "rr-test: ReviewRadar PR #20 not merged: a check is red" in host.sent


def test_running_ci_waits_without_a_message(home: Path) -> None:
    running = [{"status": "IN_PROGRESS", "conclusion": ""}]
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), checks=running)])
    agent_tick.tick_once(host, home)
    assert not host.merged() and host.posted == []
    assert not [m for m in host.sent if "not merged" in m]


def test_no_check_at_all_does_not_merge(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), checks=[])])
    agent_tick.tick_once(host, home)
    assert not host.merged()


def test_a_run_in_progress_blocks_the_merge(home: Path) -> None:
    add_run(home, "pr-20", 77)
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"))], alive_pids={77})
    agent_tick.tick_once(host, home)
    assert not host.merged()


def test_without_ready_label_it_does_not_merge(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm"), labels=("pr:changes-requested",))])
    agent_tick.tick_once(host, home)
    assert not host.merged()


# AC6, AC7: change requests and other logins


def test_approval_by_another_login_does_nothing(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "lgtm", login="stranger"))])
    agent_tick.tick_once(host, home)
    assert not host.merged() and host.spawned == []


def test_rocket_by_another_login_is_not_a_done_mark(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "rename the button", marks=("rocket",)))],
                      reactions={101: [{"user": {"login": "stranger"}, "content": "rocket"}]})
    agent_tick.tick_once(host, home)
    assert started(host) == [PR_RUN]


def test_rocket_by_the_owner_closes_the_request(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "rename the button", marks=("rocket",)))],
                      reactions={101: [{"user": {"login": OWNER}, "content": "rocket"}]})
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_reactions_are_read_only_when_the_summary_shows_a_mark(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "rename the button"))])
    agent_tick.tick_once(host, home)
    assert not [c for c in host.calls if c[:2] == ["gh", "api"] and c[-2].endswith("reactions")]
    assert started(host) == [PR_RUN]


def test_comment_from_before_the_pull_request_was_opened_does_not_count(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "old note", when="2026-10-19T00:00:00Z"))])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_line_comment_is_a_change_request(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr()], inline_comments=[inline(301, "use a constant")])
    agent_tick.tick_once(host, home)
    assert started(host) == [PR_RUN]


def test_line_comment_with_the_owners_rocket_is_done(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr()],
                      inline_comments=[inline(301, "use a constant", marks=("rocket",))],
                      reactions={301: [{"user": {"login": OWNER}, "content": "rocket"}]})
    agent_tick.tick_once(host, home)
    assert host.spawned == []
    assert any("pulls/comments/301/reactions" in " ".join(c) for c in host.calls)


def test_redo_on_the_issue_counts_but_a_plain_issue_comment_does_not(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr()], issue_comments={5: [remark(401, "thanks")]})
    agent_tick.tick_once(host, home)
    assert host.spawned == []
    host = ReviewHost(prs=[loop_pr()], issue_comments={5: [remark(402, "/redo add a test")]})
    agent_tick.tick_once(host, home)
    assert started(host) == [PR_RUN]


def test_approval_and_open_change_request_together_run_instead_of_merge(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, "rename X"),
                                   remark(102, "lgtm", when="2026-10-22T00:00:00Z"))])
    agent_tick.tick_once(host, home)
    assert not host.merged()
    assert started(host) == [PR_RUN]


def test_loop_comment_with_the_marker_is_never_a_request(home: Path) -> None:
    host = ReviewHost(prs=[loop_pr(remark(101, f"{MARKER}\nDone in abc: renamed"))])
    agent_tick.tick_once(host, home)
    assert host.spawned == []
