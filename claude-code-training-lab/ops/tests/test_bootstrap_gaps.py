"""Spec specs/bootstrap-gaps/spec.md, AC1 to AC14: bootstrap writes a project that works as is."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap, flow_config

REPO = "acme/shop"
Run = Callable[..., int]


@pytest.fixture(autouse=True)
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return fake


@pytest.fixture(autouse=True)
def fake_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "gh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


@pytest.fixture
def target(tmp_path: Path) -> Path:
    path = tmp_path / "shop"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{REPO}.git"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


@pytest.fixture
def run(target: Path) -> Run:
    def call(*extra: str, app_dir: str = ".") -> int:
        return bootstrap.main(
            [
                "--target", str(target),
                "--repo", REPO,
                "--owner", "acme-owner",
                "--app-dir", app_dir,
                "--name", "Shop",
                "--slug", "shop",
                "--ntfy-topic", "shop-test",
                "--no-labels",
                *extra,
            ]
        )  # fmt: skip

    return call


def _app(target: Path, app_dir: str) -> Path:
    return target if app_dir == "." else target / app_dir


def _settings(target: Path, app_dir: str = ".") -> dict[str, object]:
    data: dict[str, object] = json.loads(
        (_app(target, app_dir) / ".claude/settings.json").read_text()
    )
    return data


def _allow(target: Path, app_dir: str = ".") -> list[str]:
    permissions = _settings(target, app_dir)["permissions"]
    assert isinstance(permissions, dict)
    allow: list[str] = permissions["allow"]
    return allow


# AC1, AC2, AC3


@pytest.mark.parametrize("app_dir", [".", "web"])
def test_pyproject_is_written_from_the_stub(run: Run, target: Path, app_dir: str) -> None:
    assert run(app_dir=app_dir) == 0

    data = tomllib.loads((_app(target, app_dir) / "pyproject.toml").read_text())
    assert data["project"]["name"] == "shop"
    assert data["project"]["requires-python"] == ">=3.11"
    assert data["project"].get("dependencies", []) == []
    dev = " ".join(data["dependency-groups"]["dev"])
    assert all(tool in dev for tool in ("pytest", "ruff", "mypy"))
    assert data["tool"]["uv"]["package"] is False
    assert data["tool"]["ruff"]["line-length"] == 100
    assert data["tool"]["ruff"]["lint"]["select"] == ["E", "F", "I", "UP", "B"]
    assert data["tool"]["mypy"]["strict"] is True
    assert data["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_the_stub_file_has_the_stub_suffix() -> None:
    assert (bootstrap.STUBS / "pyproject.toml.stub").is_file()
    assert not (bootstrap.STUBS / "pyproject.toml").exists()


def test_a_first_test_checks_the_flow_config(run: Run, target: Path) -> None:
    assert run() == 0

    assert (target / "tests/__init__.py").is_file()
    text = (target / "tests/test_flow_config.py").read_text()
    assert "flow_config" in text
    assert f'"{REPO}"' in text
    config = flow_config.load(target / "ops/flow.toml")
    assert config.project_repo == REPO


def test_an_existing_pyproject_is_kept_and_a_step_is_printed(
    run: Run, target: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (target / "pyproject.toml").write_text("[project]\nname = 'mine'\n")

    assert run() == 0

    out = capsys.readouterr().out
    assert (target / "pyproject.toml").read_text() == "[project]\nname = 'mine'\n"
    assert not (target / "tests").exists()
    assert "pytest" in out and "ruff" in out and "mypy" in out
    assert "uv run pytest -q" in out


def test_no_pyproject_step_when_bootstrap_writes_the_file(
    run: Run, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run() == 0

    assert "dev dependencies" not in capsys.readouterr().out


# AC4


def test_first_commit_step_mentions_uv_lock(run: Run, capsys: pytest.CaptureFixture[str]) -> None:
    assert run() == 0

    line = next(x for x in capsys.readouterr().out.splitlines() if "uv sync" in x)
    assert "uv.lock" in line


# AC5


@pytest.mark.parametrize("app_dir", [".", "web"])
def test_root_claude_md_is_about_the_new_project(run: Run, target: Path, app_dir: str) -> None:
    assert run(app_dir=app_dir) == 0

    lines = (target / "CLAUDE.md").read_text().splitlines()
    assert lines[0] == "# shop"
    first = next(x for x in lines[1:] if x.strip())
    assert "Shop" in first
    assert ("`web/`" if app_dir == "web" else "`./`") in first
    assert "Django app" not in first
    assert "ReviewRadar" not in "\n".join(lines)


def test_root_claude_md_imports_only_files_bootstrap_writes(run: Run, target: Path) -> None:
    assert run(app_dir="web") == 0

    text = (target / "CLAUDE.md").read_text()
    imports = [x[1:] for x in text.splitlines() if x.startswith("@")]
    assert imports
    assert all((target / path).is_file() for path in imports)
    assert "rules/python.md" not in text


# AC6, AC7


@pytest.mark.parametrize("app_dir", [".", "web"])
def test_no_rule_names_the_old_app(run: Run, target: Path, app_dir: str) -> None:
    assert run(app_dir=app_dir) == 0

    allow = _allow(target, app_dir)
    for gone in (
        "Edit(./reviews/**)",
        "Edit(./reviewradar/**)",
        "Bash(uv run python manage.py:*)",
        "Edit(//**/render.yaml)",
    ):
        assert gone not in allow
    assert not [x for x in allow if ".claude/skills/" in x]
    for kept in ("Bash(uv run pytest:*)", "Edit(./out/**)", "Edit(./ops/**)", "Edit(./specs/**)"):
        assert kept in allow


def test_other_rules_are_kept(run: Run, target: Path) -> None:
    source = json.loads((bootstrap.APP_ROOT / ".claude/settings.json").read_text())
    dropped = {
        "Edit(./reviews/**)",
        "Edit(./reviewradar/**)",
        "Bash(uv run python manage.py:*)",
        "Edit(//**/render.yaml)",
    }
    assert run() == 0

    kept = [
        rule
        for rule in source["permissions"]["allow"]
        if rule not in dropped and ".claude/skills/" not in rule
    ]
    renamed = [r.replace("hungle-agilityio/ai-training", REPO) for r in kept]
    allow = _allow(target)
    assert [rule for rule in allow if rule in renamed] == renamed


def test_coverage_env_is_removed(run: Run, target: Path) -> None:
    assert run() == 0

    env = _settings(target)["env"]
    assert isinstance(env, dict)
    assert "FLOW_COVERAGE_INCLUDE" not in env
    assert "FLOW_COVERAGE_FAIL_UNDER" not in env
    assert env["GH_REPO"] == REPO


# AC8, AC9


def test_code_dirs_add_edit_rules_in_order_and_tests_always(run: Run, target: Path) -> None:
    assert run("--code-dirs", "src,lib/core") == 0

    allow = _allow(target)
    rules = [r for r in allow if r in ("Edit(./src/**)", "Edit(./lib/core/**)", "Edit(./tests/**)")]
    assert rules == ["Edit(./src/**)", "Edit(./lib/core/**)", "Edit(./tests/**)"]


def test_tests_rule_is_added_without_the_flag(run: Run, target: Path) -> None:
    assert run() == 0

    assert _allow(target).count("Edit(./tests/**)") == 1


def test_tests_given_in_the_flag_is_not_doubled(run: Run, target: Path) -> None:
    assert run("--code-dirs", "tests,src") == 0

    assert _allow(target).count("Edit(./tests/**)") == 1


@pytest.mark.parametrize("bad", ["../x", "src,..", "/abs", "src/../../x", "src,,lib", ""])
def test_bad_code_dir_stops_before_writing(
    run: Run, target: Path, capsys: pytest.CaptureFixture[str], bad: str
) -> None:
    code = run("--code-dirs", bad)

    assert code == 2
    assert "--code-dirs" in capsys.readouterr().err
    assert sorted(p.name for p in target.iterdir()) == [".git"]


def test_a_step_asks_for_edit_rules_without_the_flag(
    run: Run, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run() == 0

    out = capsys.readouterr().out
    assert "Edit(./<folder>/**)" in out
    assert "agent:needs-permission" in out


def test_no_such_step_with_the_flag(run: Run, capsys: pytest.CaptureFixture[str]) -> None:
    assert run("--code-dirs", "src") == 0

    assert "Edit(./<folder>/**)" not in capsys.readouterr().out


# AC10, AC11


def test_flow_tests_are_not_copied(run: Run, target: Path) -> None:
    assert run() == 0

    assert not (target / "ops/tests").exists()
    assert (target / "ops/bootstrap.py").is_file()


def test_hook_and_skill_step_is_removed_and_the_rest_stays(run: Run, target: Path) -> None:
    assert run() == 0

    workflow = (target / ".github/workflows/checks.yml").read_text()
    assert "Hook and skill tests" not in workflow
    assert "ops/tests" not in workflow
    for step in ("Install uv", "Lint", "Types", "App tests with coverage"):
        assert f"- name: {step}" in workflow


# AC12, AC13


@pytest.mark.parametrize("app_dir", [".", "web"])
def test_no_text_points_at_the_plugins_folder(run: Run, target: Path, app_dir: str) -> None:
    assert run(app_dir=app_dir) == 0

    app = _app(target, app_dir)
    for rel in (".claude/project-instructions.md", ".claude/rules/security.md"):
        assert "../plugins/" not in (app / rel).read_text()


def test_route_issue_command_reads_as_the_installed_plugin_skill(run: Run, target: Path) -> None:
    assert run() == 0

    text = (target / ".claude/project-instructions.md").read_text()
    line = next(x for x in text.splitlines() if "route_issue.py" in x)
    assert "installed agent-flow plugin" in line
    assert "`create-issue`" in line
    assert "base directory" in line
    assert "one plain command" in line


def test_plugin_files_are_named_inside_the_installed_plugin(run: Run, target: Path) -> None:
    assert run() == 0

    text = (target / ".claude/rules/security.md").read_text()
    assert re.search(r"`skills/share-report/rules\.md`[^.]*installed agent-flow plugin", text)
    assert re.search(r"`hooks/README\.md`[^.]*installed agent-flow plugin", text)


def test_test_folder_in_instructions_is_tests(run: Run, target: Path) -> None:
    assert run() == 0

    text = (target / ".claude/project-instructions.md").read_text()
    assert "reviews/tests/" not in text
    assert "an existing test under `tests/`" in text


# AC14


def test_install_step_has_the_project_scope(run: Run, capsys: pytest.CaptureFixture[str]) -> None:
    assert run() == 0

    out = capsys.readouterr().out
    assert "claude plugin install agent-flow@ai-training --scope project" in out


def test_the_guide_says_the_same_install_command() -> None:
    text = (Path(bootstrap.__file__).parent / "BOOTSTRAP.md").read_text()

    assert "claude plugin install agent-flow@ai-training --scope project" in text
