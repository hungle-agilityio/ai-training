"""Tests of the rule that a loop pull request carries the verify report link."""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "before-github-command-check.py"
LINK = "https://claude.ai/artifact/0f3c2a"
REASON = "a loop pull request needs the verify report link (share-report)"


def run_hook(command: str, cwd: Path, loop: bool) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key != "REVIEWRADAR_LOOP"}
    if loop:
        env["REVIEWRADAR_LOOP"] = "1"
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    return subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_loop_pull_request_without_the_link_is_denied(tmp_path: Path) -> None:
    done = run_hook('gh pr create --base main --title t --body "no link"', tmp_path, loop=True)
    assert done.returncode == 2
    assert REASON in done.stderr


def test_loop_pull_request_with_the_link_in_body_is_allowed(tmp_path: Path) -> None:
    command = f'gh pr create --base main --title t --body "Report (private link): {LINK}"'
    done = run_hook(command, tmp_path, loop=True)
    assert done.returncode == 0
    assert done.stdout == ""


def test_loop_pull_request_with_the_link_in_short_body_flag_is_allowed(tmp_path: Path) -> None:
    done = run_hook(f"gh pr create --title t -b 'see {LINK}'", tmp_path, loop=True)
    assert done.returncode == 0


def test_loop_pull_request_with_the_link_in_body_file_is_allowed(tmp_path: Path) -> None:
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "pr-body.md").write_text(f"<!-- work-queue -->\nReport: {LINK}\n")
    for flag in ("--body-file out/pr-body.md", "-F out/pr-body.md", "--body-file=out/pr-body.md"):
        done = run_hook(f"gh pr create --base main --title t {flag}", tmp_path, loop=True)
        assert done.returncode == 0, flag


def test_loop_pull_request_with_a_body_file_without_the_link_is_denied(tmp_path: Path) -> None:
    (tmp_path / "pr-body.md").write_text("Report: not shared (local file: out/verify/x)\n")
    done = run_hook("gh pr create --title t --body-file pr-body.md", tmp_path, loop=True)
    assert done.returncode == 2
    assert REASON in done.stderr


def test_loop_pull_request_with_an_unreadable_body_file_is_denied(tmp_path: Path) -> None:
    for flag in ("--body-file missing.md", "-F -"):
        done = run_hook(f"gh pr create --title t {flag}", tmp_path, loop=True)
        assert done.returncode == 2, flag
        assert REASON in done.stderr


def test_loop_pull_request_with_fill_is_denied(tmp_path: Path) -> None:
    done = run_hook("gh pr create --fill", tmp_path, loop=True)
    assert done.returncode == 2
    assert REASON in done.stderr


def test_the_link_after_the_command_does_not_count(tmp_path: Path) -> None:
    done = run_hook(f"gh pr create --fill && echo {LINK}", tmp_path, loop=True)
    assert done.returncode == 2


def test_interactive_pull_request_asks_with_or_without_the_link(tmp_path: Path) -> None:
    for body in ('--body "no link"', f'--body "{LINK}"', "--fill"):
        done = run_hook(f"gh pr create --title t {body}", tmp_path, loop=False)
        assert done.returncode == 0, body
        reply = json.loads(done.stdout)["hookSpecificOutput"]
        assert reply["permissionDecision"] == "ask"


def test_other_loop_commands_are_not_checked_for_the_link(tmp_path: Path) -> None:
    done = run_hook("gh pr view 5 --json state", tmp_path, loop=True)
    assert done.returncode == 0
    assert done.stdout == ""
