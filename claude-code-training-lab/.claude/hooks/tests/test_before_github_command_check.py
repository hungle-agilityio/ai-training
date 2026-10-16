"""Tests for the GitHub guard hook. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import json
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-github-command-check.py"
ALLOWED = "hungle-agilityio/ai-training"


def load_guard() -> ModuleType:
    spec = util.spec_from_file_location("guard", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load_guard()


def problems(command: str) -> list[str]:
    result: list[str] = GUARD.check_command(command, ALLOWED)
    return result


MAY_RUN = [
    "uv run pytest -q --no-cov",
    "echo hello",
    "ls -R docs",
    "cp -R a b",
    "git status",
    "git diff --stat",
    "git log --oneline -5",
    "git add -A",
    'git commit -m "Fix the thing"',
    "git commit -m 'see https://github.com/other/repo for details'",
    "git push -u origin feat/x",
    "git push origin main",
    "git push",
    "git pull --rebase origin main",
    "git fetch origin",
    "git fetch --all",
    "git remote -v",
    "git remote add origin git@github.com:hungle-agilityio/ai-training.git",
    "git remote set-url origin https://github.com/hungle-agilityio/ai-training.git",
    "git push https://github.com/hungle-agilityio/ai-training.git main",
    "gh --version",
    "git config --get remote.origin.url",
    "git config user.email x@example.com",
    "ssh -T git@github.com",
    "ssh -T -o BatchMode=yes -o ConnectTimeout=8 git@github.com",
    "ssh user@example.com ls",
    "python3 - <<'EOF'\nprint('gh repo list is only text here')\nEOF",
    "cat <<'EOF' > notes.md\ngh auth login is described here\nEOF",
    "gh auth status",
    "gh issue create --title x --body y",
    "gh issue list",
    "gh issue view 3",
    "gh issue list -R hungle-agilityio/ai-training",
    "gh issue list -R HungLe-Agilityio/AI-Training",
    "gh issue list --repo=hungle-agilityio/ai-training",
    "gh issue view https://github.com/hungle-agilityio/ai-training/issues/1",
    "gh pr create --title t --body b",
    "gh pr view 2 --json state",
    "gh label create naming",
    "gh repo view",
    "gh repo view hungle-agilityio/ai-training",
    "gh api repos/hungle-agilityio/ai-training/issues",
    "gh api user",
    "GH_REPO=hungle-agilityio/ai-training gh issue list",
    "git status && gh issue list",
    "curl -s https://api.github.com/repos/hungle-agilityio/ai-training/issues",
]

MUST_BLOCK = [
    "git config remote.origin.url https://github.com/cli/cli.git",
    "git config remote.origin.pushurl git@github.com:cli/cli.git",
    "git config --global url.git@github.com:.insteadOf x",
    "ssh git@github.com git-upload-pack 'cli/cli.git'",
    "scp file git@github.com:cli/cli.git",
    "ssh -T git@github.com git-upload-pack 'cli/cli.git'",
    "ssh git@github.com",
    "bash <<'EOF'\ngh repo list\nEOF",
    "bash -c 'gh repo list'",
    "cat <<'EOF' | sh\ngh repo list\nEOF",
    'echo "$(gh repo list)"',
    "gh repo list",
    "gh repo create foo --private",
    "gh repo delete hungle-agilityio/ai-training",
    "gh repo view cli/cli",
    "gh repo clone cli/cli",
    "gh auth login",
    "gh auth logout",
    "gh auth refresh -s delete_repo",
    "gh gist create f",
    "gh ssh-key list",
    "gh secret list",
    "gh search repos x",
    "gh org list",
    "gh foo bar",
    "gh issue list -R cli/cli",
    "gh issue list --repo=cli/cli",
    "gh issue list -R other",
    "gh issue view https://github.com/cli/cli/issues/1",
    "GH_REPO=cli/cli gh issue list",
    "gh api repos/cli/cli",
    "gh api /repos/cli/cli/issues",
    "gh api user/repos",
    "gh api graphql -f query=x",
    "gh api -X DELETE repos/hungle-agilityio/ai-training/issues/1",
    "gh api --method DELETE repos/hungle-agilityio/ai-training/issues/1",
    "git push https://github.com/cli/cli.git main",
    "git push otherremote main",
    "git remote add upstream https://github.com/cli/cli.git",
    "git remote add origin git@gitlab.asoft-python.com:hung.le/ai-training.git",
    "git remote set-url origin https://github.com/cli/cli.git",
    "git remote add origin ./somewhere",
    "git clone https://github.com/cli/cli",
    "git fetch https://github.com/cli/cli.git",
    "git config url.https://x.insteadOf y",
    "git -C /tmp/x push https://github.com/cli/cli.git",
    "curl https://api.github.com/repos/cli/cli",
    "curl -s https://api.github.com/user/repos",
    "wget https://github.com/cli/cli/archive/x.zip",
    "git status && gh repo list",
    "echo $(gh repo list)",
    "git add -A; gh issue list -R cli/cli",
    'git commit -m "x" && git push https://github.com/cli/cli.git',
]


@pytest.mark.parametrize("command", MAY_RUN)
def test_command_may_run(command: str) -> None:
    assert problems(command) == []


@pytest.mark.parametrize("command", MUST_BLOCK)
def test_command_is_blocked(command: str) -> None:
    assert problems(command) != []


def run_hook(payload: object, allowed_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )


def bash(command: str) -> dict[str, object]:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def test_hook_exit_code_blocks_with_a_message() -> None:
    result = run_hook(bash("gh repo list"))
    assert result.returncode == 2
    assert ALLOWED in result.stderr


def test_hook_exit_code_allows_normal_command() -> None:
    assert run_hook(bash("git status")).returncode == 0
    assert run_hook(bash("uv run pytest -q")).returncode == 0


def test_hook_ignores_other_tools_and_bad_input() -> None:
    assert run_hook({"tool_name": "Read", "tool_input": {"file_path": "x"}}).returncode == 0
    result = subprocess.run(
        [sys.executable, "-I", str(HOOK)], input="not json", capture_output=True, text=True,
        check=False,
    )
    assert result.returncode == 0
