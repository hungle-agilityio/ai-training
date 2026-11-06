"""ops/check_plugin_version.py: a plugin change needs a new version. Run: pytest ops/tests"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ops import check_plugin_version

MANIFEST = "plugins/agent-flow/.claude-plugin/plugin.json"


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return done.stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def commit(repo: Path, message: str) -> str:
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def set_version(repo: Path, version: str) -> None:
    write(repo, MANIFEST, json.dumps({"name": "agent-flow", "version": version}))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    set_version(tmp_path, "1.0.2")
    write(tmp_path, "plugins/agent-flow/hooks/guard.py", "a = 1\n")
    write(tmp_path, "app/views.py", "b = 1\n")
    commit(tmp_path, "base")
    return tmp_path


def run(repo: Path, base: str, head: str, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = check_plugin_version.main([base, head, "--repo", str(repo)])
    return code, capsys.readouterr().out


def test_plugin_change_without_new_version_fails(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "plugins/agent-flow/hooks/guard.py", "a = 2\n")
    head = commit(repo, "change the hook")
    code, out = run(repo, base, head, capsys)
    assert code == 1
    assert out.strip() == (
        "plugins/agent-flow/ changed but .claude-plugin/plugin.json still has version 1.0.2"
    )


def test_plugin_change_with_new_version_passes(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "plugins/agent-flow/hooks/guard.py", "a = 2\n")
    set_version(repo, "1.0.3")
    head = commit(repo, "change the hook and bump")
    assert run(repo, base, head, capsys)[0] == 0


def test_change_outside_the_plugin_passes(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "app/views.py", "b = 2\n")
    head = commit(repo, "change the app")
    assert run(repo, base, head, capsys)[0] == 0


def test_only_changes_since_the_merge_base_count(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "switch", "-q", "-c", "feature")
    write(repo, "app/views.py", "b = 2\n")
    head = commit(repo, "app only")
    git(repo, "switch", "-q", "main")
    write(repo, "plugins/agent-flow/hooks/guard.py", "a = 3\n")
    main_head = commit(repo, "plugin change on main")
    assert base != main_head
    assert run(repo, main_head, head, capsys)[0] == 0


def test_new_plugin_without_a_manifest_at_base_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    git(tmp_path, "init", "-q", "-b", "main")
    write(tmp_path, "README.md", "x\n")
    base = commit(tmp_path, "base")
    set_version(tmp_path, "1.0.0")
    write(tmp_path, "plugins/agent-flow/hooks/guard.py", "a = 1\n")
    head = commit(tmp_path, "add the plugin")
    assert run(tmp_path, base, head, capsys)[0] == 0


def test_base_that_moved_its_version_still_needs_a_new_one(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    git(repo, "switch", "-q", "-c", "feature")
    write(repo, "plugins/agent-flow/hooks/guard.py", "a = 2\n")
    head = commit(repo, "hook change, no bump")
    git(repo, "switch", "-q", "main")
    set_version(repo, "1.0.3")
    main_head = commit(repo, "bump on main")
    code, out = run(repo, main_head, head, capsys)
    assert code == 1
    assert "still has version 1.0.2" in out
