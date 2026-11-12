"""review_level.py says "high" when a branch touches a sensitive path of the flow config.

Run: uv run pytest ../plugins/agent-flow/skills/work-queue/tests --no-cov -q (from the app folder)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "review_level.py"
PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
FLOW_CONFIG_PY = PROJECT / "ops" / "flow_config.py"
CONFIG = """\
[project]
repo = "acme/shop"
owner = "acme-owner"
app_dir = "app"
display_name = "Shop"
slug = "shop"

[loop]
state_dir = "~/.shop"
tmux_session = "shop-loop"
launchd_label = "com.shop.loop"
setup_command = ["npm", "ci"]
alone_words = []

[checks]
commands = [["bash", "scripts/check.sh"]]
ci_workflow = "Checks"
protected_test_dirs = ["tests"]

[release]
timezone = "Europe/Berlin"
deploy_line = ""

[paths]
review_sensitive = ["shop/models.py", "shop/migrations/*", "../deploy.yaml"]
"""
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Tester",
    "GIT_AUTHOR_EMAIL": "tester@example.com",
    "GIT_COMMITTER_NAME": "Tester",
    "GIT_COMMITTER_EMAIL": "tester@example.com",
}


def git(root: Path, *args: str) -> None:
    env = {**os.environ, **GIT_ENV}
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True, text=True)


def write(root: Path, name: str, text: str = "x\n") -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repository on branch work, forked from main; the app folder is app/."""
    app = tmp_path / "app"
    (app / "ops").mkdir(parents=True)
    (app / "ops" / "flow.toml").write_text(CONFIG, encoding="utf-8")
    shutil.copy(FLOW_CONFIG_PY, app / "ops" / "flow_config.py")
    write(tmp_path, "app/shop/models.py", "v1\n")
    write(tmp_path, "app/shop/views.py", "v1\n")
    write(tmp_path, "deploy.yaml", "v1\n")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "work")
    return tmp_path


def commit(root: Path, name: str) -> None:
    write(root, name, "v2\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "change")


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "FLOW_CONFIG")}
    env.update(GIT_ENV)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=root / "app",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_committed_change_to_a_sensitive_file_prints_high_and_the_file_line(repo: Path) -> None:
    commit(repo, "app/shop/models.py")
    done = run(repo, "--base", "main")
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == ["high", "  app/shop/models.py  (shop/models.py)"]


def test_a_change_at_the_repository_root_matches_a_parent_folder_pattern(repo: Path) -> None:
    commit(repo, "deploy.yaml")
    done = run(repo, "--base", "main")
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == ["high", "  deploy.yaml  (../deploy.yaml)"]


def test_uncommitted_and_new_files_are_matched_and_listed_sorted(repo: Path) -> None:
    write(repo, "app/shop/models.py", "v2\n")
    write(repo, "app/shop/migrations/0002_x.py")
    done = run(repo, "--base", "main")
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == [
        "high",
        "  app/shop/migrations/0002_x.py  (shop/migrations/*)",
        "  app/shop/models.py  (shop/models.py)",
    ]


def test_a_file_changed_twice_is_listed_once(repo: Path) -> None:
    commit(repo, "app/shop/models.py")
    write(repo, "app/shop/models.py", "v3\n")
    done = run(repo, "--base", "main")
    assert done.stdout.splitlines() == ["high", "  app/shop/models.py  (shop/models.py)"]


def test_a_branch_that_changes_only_a_plain_file_prints_standard(repo: Path) -> None:
    commit(repo, "app/shop/views.py")
    done = run(repo, "--base", "main")
    assert done.returncode == 0, done.stderr
    assert done.stdout == "standard\n"


def test_a_branch_with_no_change_prints_standard(repo: Path) -> None:
    done = run(repo, "--base", "main")
    assert done.returncode == 0, done.stderr
    assert done.stdout == "standard\n"


def test_a_config_without_review_sensitive_prints_standard(repo: Path) -> None:
    config = repo / "app" / "ops" / "flow.toml"
    config.write_text(CONFIG.split("[paths]")[0], encoding="utf-8")
    commit(repo, "app/shop/models.py")
    done = run(repo, "--base", "main")
    assert done.returncode == 0, done.stderr
    assert done.stdout == "standard\n"


def test_an_unknown_base_exits_2_with_a_review_level_message_on_stderr(repo: Path) -> None:
    done = run(repo, "--base", "no-such-ref")
    assert done.returncode == 2
    assert done.stdout == ""
    assert done.stderr.startswith("review_level: ")
    assert len(done.stderr.strip().splitlines()) == 1


def test_a_missing_config_exits_2_with_a_review_level_message_on_stderr(repo: Path) -> None:
    (repo / "app" / "ops" / "flow.toml").unlink()
    done = run(repo, "--base", "main")
    assert done.returncode == 2
    assert done.stderr.startswith("review_level: ")
