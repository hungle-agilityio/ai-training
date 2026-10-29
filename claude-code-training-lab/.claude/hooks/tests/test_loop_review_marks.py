"""Loop builds mark change requests (ADR-016). Run: uv run pytest .claude/hooks/tests --no-cov"""

import json
import os
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parents[1]
LAB = HOOKS.parents[1]
GITHUB_HOOK = HOOKS / "before-github-command-check.py"
ALLOWED = "hungle-agilityio/ai-training"
REPO = f"repos/{ALLOWED}"
RESOLVE = (
    "gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: \"PRRT_kwDO1a\"})"
    " { thread { isResolved } } }'"
)


def load() -> ModuleType:
    spec = util.spec_from_file_location("guard_marks", GITHUB_HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load()


def no_git(args: list[str]) -> tuple[int, str]:
    return 0, "task/79-x\n"


def decide(command: str, loop: bool) -> str:
    if GUARD.check_command(command, ALLOWED, loop):
        return "deny"
    decision: str = GUARD.check_publish(command, loop, no_git, ALLOWED)[0]
    return decision


def run_hook(command: str, loop: bool) -> subprocess.CompletedProcess[str]:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(LAB)}
    env = {key: value for key, value in os.environ.items() if key != "REVIEWRADAR_LOOP"}
    if loop:
        env["REVIEWRADAR_LOOP"] = "1"
    return subprocess.run(
        [sys.executable, "-I", str(GITHUB_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


ALLOWED_MARKS = [
    f"gh api -X POST {REPO}/issues/comments/123/reactions -f content=eyes",
    f"gh api -X POST {REPO}/issues/comments/123/reactions -f content=rocket",
    f"gh api --method POST {REPO}/pulls/comments/456/reactions -f content=confused",
    f"gh api -X POST {REPO}/pulls/comments/456/reactions -f content=rocket --silent",
    f"gh api -X POST {REPO}/pulls/80/comments/456/replies -f body='Done in abc1234: renamed it'",
    RESOLVE,
    "gh api graphql -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id})"
    " { thread { id isResolved } } }' -f threadId=PRRT_kwDO1a",
]


@pytest.mark.parametrize("command", ALLOWED_MARKS)
def test_review_mark_is_allowed_without_asking_in_loop(command: str) -> None:
    assert decide(command, True) == "allow"


@pytest.mark.parametrize("command", ALLOWED_MARKS)
def test_hook_answers_allow_for_a_review_mark_in_loop(command: str) -> None:
    done = run_hook(command, loop=True)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"] == "allow"


REFUSED_IN_LOOP = [
    "gh api -X POST repos/other/repo/issues/comments/123/reactions -f content=rocket",
    "gh api -X POST repos/other/repo/pulls/80/comments/456/replies -f body=x",
    f"gh api -X DELETE {REPO}/issues/comments/123/reactions/9",
    f"gh api -X POST {REPO}/issues/comments/123/reactions -f content=heart",
    f"gh api -X POST {REPO}/issues/comments/123/reactions -f content=rocket -f extra=1",
    f"gh api -X POST {REPO}/pulls/comments/456/reactions --input body.json",
    "gh api graphql -f query='mutation { mergePullRequest(input: {pullRequestId: \"PR_1\"})"
    " { pullRequest { merged } } }'",
    "gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: \"PRRT_1\"})"
    " { thread { isResolved } } addComment(input: {subjectId: \"I_1\", body: \"x\"})"
    " { clientMutationId } }'",
    "gh api graphql -f query='query { viewer { login } }'",
    "gh pr merge 80 --merge --match-head-commit abc1234",
]


@pytest.mark.parametrize("command", REFUSED_IN_LOOP)
def test_other_calls_are_refused_in_loop(command: str) -> None:
    assert decide(command, True) == "deny"


def test_hook_exits_2_for_another_graphql_mutation_in_loop() -> None:
    command = (
        "gh api graphql -f query='mutation { mergePullRequest(input: {pullRequestId: \"PR_1\"})"
        " { pullRequest { merged } } }'"
    )
    assert run_hook(command, loop=True).returncode == 2


def test_other_gh_api_reads_stay_as_today_in_loop() -> None:
    assert decide(f"gh api {REPO}/pulls/80", True) == "allow"
    assert GUARD.check_publish(f"gh api {REPO}/pulls/80", True, no_git, ALLOWED)[1] == []


@pytest.mark.parametrize("command", ALLOWED_MARKS[:5] + [f"gh api {REPO}/issues"])
def test_gh_api_still_asks_outside_loop(command: str) -> None:
    assert decide(command, False) == "ask"


def test_resolve_mutation_is_refused_outside_loop() -> None:
    assert decide(RESOLVE, False) == "deny"


def test_settings_allow_the_review_marks_and_no_longer_ask_for_every_gh_api() -> None:
    settings = json.loads((LAB / ".claude" / "settings.json").read_text())
    allow = settings["permissions"]["allow"]
    assert f"Bash(gh api -X POST {REPO}/issues/comments/*/reactions *)" in allow
    assert f"Bash(gh api -X POST {REPO}/pulls/comments/*/reactions *)" in allow
    assert f"Bash(gh api -X POST {REPO}/pulls/*/comments/*/replies *)" in allow
    assert "Bash(gh api graphql *)" in allow


THREADS = (
    "gh api graphql -F number=80 -f query='query($number: Int!) { repository(owner: "
    "\"hungle-agilityio\", name: \"ai-training\") { pullRequest(number: $number) "
    "{ reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) "
    "{ nodes { databaseId } } } } } } }'"
)


def test_loop_may_read_the_review_threads_it_resolves() -> None:
    assert decide(THREADS, True) == "allow"


@pytest.mark.parametrize(
    "command",
    [
        THREADS.replace("ai-training", "other"),
        THREADS.replace("query($number", "mutation($number"),
        THREADS.replace("reviewThreads(first: 100)", "files(first: 100)"),
    ],
)
def test_other_graphql_reads_are_refused_in_loop(command: str) -> None:
    assert decide(command, True) == "deny"
