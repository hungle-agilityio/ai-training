"""Spec specs/flow-bootstrap/spec.md, AC21 to AC31: ops/bootstrap.py sets up a new repository."""

from __future__ import annotations

import os
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap, flow_config

REPO = "acme/shop"
OWNER = "acme-owner"
OLD_VALUES = (
    "hungle-agilityio",
    "claude-code-training-lab",
    "ReviewRadar",
    "rr-loop",
)
Run = Callable[..., int]


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _clone(path: Path, origin: str = f"https://github.com/{REPO}.git") -> Path:
    path.mkdir()
    _git("init", "-q", cwd=path)
    _git("remote", "add", "origin", origin, cwd=path)
    return path


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return fake


@pytest.fixture
def gh_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake `gh` first on PATH; it logs its arguments and fails for the label `epic`."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "gh.log"
    script = bin_dir / "gh"
    script.write_text(
        f'#!/bin/sh\necho "$@" >> "{log}"\n[ "$3" = "epic" ] && exit 1\nexit 0\n',
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return log


@pytest.fixture
def target(tmp_path: Path) -> Path:
    return _clone(tmp_path / "shop")


@pytest.fixture
def run(target: Path) -> Run:
    def call(*extra: str, app_dir: str = ".", skip: tuple[str, ...] = ()) -> int:
        values = {
            "--target": str(target),
            "--repo": REPO,
            "--owner": OWNER,
            "--app-dir": app_dir,
            "--name": "Shop",
            "--slug": "shop",
            "--ntfy-topic": "shop-test",
        }
        argv: list[str] = []
        for flag, value in values.items():
            if flag not in skip:
                argv += [flag, value]
        return bootstrap.main([*argv, *extra])

    return call


def _text_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]


def test_missing_values_are_listed_in_one_message(
    run: Run, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    code = run(skip=("--repo", "--slug", "--ntfy-topic"))

    err = capsys.readouterr().err
    assert code == 2
    assert err.count("\n") == 1
    assert "--repo" in err and "--slug" in err and "--ntfy-topic" in err
    assert "--owner" not in err


@pytest.mark.parametrize("slug", ["Shop", "1shop", "s", "shop_x", "a" * 32])
def test_bad_slug_is_refused(
    slug: str, target: Path, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    code = bootstrap.main(
        [
            "--target",
            str(target),
            "--repo",
            REPO,
            "--owner",
            OWNER,
            "--app-dir",
            ".",
            "--name",
            "Shop",
            "--slug",
            slug,
            "--ntfy-topic",
            "t",
            "--dry-run",
        ],
    )

    assert code == 2
    assert "slug" in capsys.readouterr().err


@pytest.mark.parametrize(
    "origin",
    [
        "https://github.com/acme/shop",
        "https://github.com/acme/shop.git",
        "git@github.com:acme/shop.git",
        "ssh://git@github.com/acme/shop.git",
    ],
)
def test_origin_forms_of_the_repo_are_accepted(
    origin: str, tmp_path: Path, home: Path, gh_log: Path
) -> None:
    clone = _clone(tmp_path / "other", origin)

    code = bootstrap.main(
        [
            "--target",
            str(clone),
            "--repo",
            REPO,
            "--owner",
            OWNER,
            "--app-dir",
            ".",
            "--name",
            "Shop",
            "--slug",
            "shop",
            "--ntfy-topic",
            "t",
            "--no-labels",
        ],
    )

    assert code == 0


def test_other_origin_is_refused_and_nothing_is_written(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    clone = _clone(tmp_path / "other", "https://github.com/someone/else.git")

    code = bootstrap.main(
        [
            "--target",
            str(clone),
            "--repo",
            REPO,
            "--owner",
            OWNER,
            "--app-dir",
            ".",
            "--name",
            "Shop",
            "--slug",
            "shop",
            "--ntfy-topic",
            "t",
            "--no-labels",
        ],
    )

    assert code == 2
    assert "someone/else" in capsys.readouterr().err
    assert _text_files(clone) == []


def test_folder_that_is_not_a_clone_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()

    code = bootstrap.main(
        [
            "--target",
            str(plain),
            "--repo",
            REPO,
            "--owner",
            OWNER,
            "--app-dir",
            ".",
            "--name",
            "Shop",
            "--slug",
            "shop",
            "--ntfy-topic",
            "t",
            "--no-labels",
        ],
    )

    assert code == 2
    assert "git" in capsys.readouterr().err


def test_manifest_lists_what_is_copied_and_every_listed_file_lands_in_the_target(
    run: Run, target: Path, home: Path
) -> None:
    assert run("--no-labels") == 0

    for expected in (
        "ops/agent_tick.py",
        "ops/flow_config.py",
        "ops/bootstrap.py",
        "ops/tests/test_agent_tick.py",
        ".claude/settings.json",
        ".claude/skills/work-queue/SKILL.md",
        ".claude/rules/workflow.md",
        ".claude/knowledge/decisions/ADR-018-stacked-pull-requests-and-retries.md",
        ".claude/knowledge/decisions/README.md",
        "docs/app/templates/spec/spec.md",
        "specs/README.md",
        ".claude/project-instructions.md",
        "CLAUDE.md",
        ".github/ISSUE_TEMPLATE/task.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/workflows/checks.yml",
    ):
        assert (target / expected).is_file(), expected
    assert not (target / "reviews").exists()
    assert not (target / ".claude/skills/diagnose-bug").exists()


def test_entry_that_does_not_exist_is_reported_and_skipped(
    run: Run, capsys: pytest.CaptureFixture[str], target: Path, home: Path
) -> None:
    source = Path(bootstrap.__file__).resolve().parent.parent
    adr = source / ".claude/knowledge/decisions/ADR-019-flow-config-and-bootstrap.md"
    expected_missing = not adr.exists()

    assert run("--no-labels") == 0

    out = capsys.readouterr().out
    skipped = "skipped, not found in the source: .claude/knowledge/decisions/ADR-019"
    assert (skipped in out) is expected_missing


def test_app_folder_goes_under_the_target_and_checks_workflow_points_at_it(
    run: Run, target: Path, home: Path
) -> None:
    assert run("--no-labels", app_dir="web") == 0

    assert (target / "web/ops/agent_tick.py").is_file()
    assert not (target / "web/.claude/hooks").exists()
    assert (target / "CLAUDE.md").is_file()
    workflow = (target / ".github/workflows/checks.yml").read_text()
    assert "working-directory: web" in workflow
    assert "@web/.claude/CLAUDE.md" in (target / "CLAUDE.md").read_text()


def test_workflow_working_directory_is_dot_for_app_dir_dot(
    run: Run, target: Path, home: Path
) -> None:
    assert run("--no-labels") == 0

    workflow = (target / ".github/workflows/checks.yml").read_text()
    assert "working-directory: .\n" in workflow
    assert "@.claude/CLAUDE.md" in (target / "CLAUDE.md").read_text()
    assert "@./" not in (target / "CLAUDE.md").read_text()


def test_flow_toml_has_the_six_values_and_defaults_and_loads(
    run: Run, target: Path, home: Path
) -> None:
    assert run("--no-labels", app_dir="web") == 0

    config = flow_config.load(target / "web/ops/flow.toml")
    assert config.project_repo == REPO
    assert config.project_owner == OWNER
    assert config.project_app_dir == "web"
    assert config.project_display_name == "Shop"
    assert config.project_slug == "shop"
    assert config.loop_state_dir == Path("~/.shop").expanduser()
    assert config.loop_tmux_session == "shop-loop"
    assert config.loop_launchd_label == "com.shop.loop"
    assert config.loop_setup_command == ("uv", "sync", "--frozen")
    assert config.loop_alone_words == ()
    assert config.checks_commands == (
        ("uv", "run", "ruff", "check", "."),
        ("uv", "run", "mypy", "."),
        ("uv", "run", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider"),
    )
    assert config.checks_ci_workflow == "Checks"
    assert config.checks_protected_test_dirs == ("tests",)
    assert config.release_timezone == "Asia/Ho_Chi_Minh"
    assert config.release_deploy_line == ""


@pytest.mark.parametrize("app_dir", [".", "web"])
def test_no_old_value_is_left_in_any_copied_file(
    run: Run, target: Path, home: Path, app_dir: str
) -> None:
    assert run("--no-labels", app_dir=app_dir) == 0

    for path in _text_files(target):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for old in OLD_VALUES:
            assert old not in text, f"{old} left in {path.relative_to(target)}"


def test_allowed_repo_file_starts_with_the_new_repo(run: Run, target: Path, home: Path) -> None:
    assert run("--no-labels") == 0

    assert not (target / ".claude/hooks/github-allowed-repo.txt").exists()


def test_stubs_have_headings_and_the_todo_line(run: Run, target: Path, home: Path) -> None:
    assert run("--no-labels", app_dir="web") == 0

    for name in (".claude/CLAUDE.md", ".claude/rules/architecture.md", ".claude/rules/domain.md"):
        text = (target / "web" / name).read_text()
        assert "TODO: fill in for Shop" in text
        assert text.startswith("# ")
        assert "\n## " in text or name.endswith("domain.md")


def test_coverage_step_is_removed_from_the_checks_workflow(
    run: Run, target: Path, home: Path
) -> None:
    assert run("--no-labels") == 0

    workflow = (target / ".github/workflows/checks.yml").read_text()
    assert "coverage report" not in workflow
    assert "Coverage gate" not in workflow
    assert "Hook and skill tests" in workflow


def test_eighteen_labels_are_created_with_force_and_a_failed_one_does_not_stop_the_rest(
    run: Run, gh_log: Path, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    code = run()

    calls = gh_log.read_text().splitlines()
    assert len(calls) == 18
    assert all(call.startswith("label create ") for call in calls)
    assert all(call.endswith("--force -R acme/shop") for call in calls)
    assert any(
        call.startswith("label create agent:ready --color 0E8A16 --description") for call in calls
    )
    assert "epic" in capsys.readouterr().err
    assert code == 0


def test_label_description_uses_the_display_name(run: Run, gh_log: Path, home: Path) -> None:
    run()

    app_label = next(c for c in gh_log.read_text().splitlines() if " area:app " in c)
    assert "Shop" in app_label and OLD_VALUES[2] not in app_label


def test_no_labels_runs_no_gh(run: Run, gh_log: Path, home: Path) -> None:
    run("--no-labels")

    assert not gh_log.exists()


def test_agent_env_is_written_from_the_example(
    run: Run, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/somewhere/claude")

    assert run("--no-labels") == 0

    lines = (home / ".shop/agent.env").read_text().splitlines()
    assert "AGENT_CONCURRENCY=1" in lines
    assert "NTFY_TOPIC=shop-test" in lines
    assert "CLAUDE_CODE_ENTRYPOINT=claude-desktop" in lines
    assert "CLAUDE_CONFIG_DIR=/somewhere/claude" in lines
    assert "AGENT_CONCURRENCY=2" not in lines


def test_agent_env_has_no_config_dir_line_when_the_variable_is_unset(run: Run, home: Path) -> None:
    assert run("--no-labels") == 0

    lines = (home / ".shop/agent.env").read_text().splitlines()
    assert not any(line.startswith("CLAUDE_CONFIG_DIR=") for line in lines)


def test_existing_agent_env_is_kept_and_the_run_goes_on(
    run: Run, home: Path, capsys: pytest.CaptureFixture[str], target: Path
) -> None:
    (home / ".shop").mkdir()
    (home / ".shop/agent.env").write_text("MINE=1\n")

    code = run("--no-labels")

    assert code == 0
    assert (home / ".shop/agent.env").read_text() == "MINE=1\n"
    assert "agent.env" in capsys.readouterr().out
    assert (target / "ops/flow.toml").is_file()


def test_existing_files_are_all_listed_and_nothing_is_written(
    run: Run, target: Path, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    (target / "CLAUDE.md").write_text("mine\n")
    (target / "ops").mkdir()
    (target / "ops/flow.toml").write_text("mine\n")

    code = run("--no-labels")

    err = capsys.readouterr().err
    assert code == 2
    assert "CLAUDE.md" in err and "flow.toml" in err
    assert (target / "CLAUDE.md").read_text() == "mine\n"
    assert not (target / "ops/agent_tick.py").exists()
    assert not (home / ".shop").exists()


def test_running_twice_stops_at_the_second_run(
    run: Run, capsys: pytest.CaptureFixture[str], home: Path
) -> None:
    assert run("--no-labels") == 0
    capsys.readouterr()

    assert run("--no-labels") == 2
    assert "already exist" in capsys.readouterr().err


def test_only_label_create_is_ever_run_with_gh_and_git_is_read_only(
    run: Run, gh_log: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []
    real = subprocess.run

    def spy(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(list(cmd))
        return real(cmd, *args, **kwargs)  # type: ignore[call-overload, no-any-return]

    monkeypatch.setattr(subprocess, "run", spy)

    run()

    gh = [c for c in seen if c[0] == "gh"]
    git = [c for c in seen if c[0] == "git"]
    assert gh and all(c[1:3] == ["label", "create"] for c in gh)
    forbidden = {"commit", "push", "add", "checkout", "reset"}
    assert not any(forbidden & set(c) for c in git)


def test_dry_run_prints_the_plan_and_writes_nothing(
    run: Run, gh_log: Path, target: Path, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run("--dry-run")

    out = capsys.readouterr().out
    assert code == 0
    assert "ops/agent_tick.py" in out
    assert "ops/flow.toml" in out
    assert "agent:ready" in out
    assert str(home / ".shop/agent.env") in out
    assert out.count("\n8. ") == 1
    assert _text_files(target) == []
    assert not (home / ".shop").exists()
    assert not gh_log.exists()


def test_the_eight_steps_are_printed_at_the_end(
    run: Run, home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("--no-labels", app_dir="web") == 0

    out = capsys.readouterr().out
    for number in range(1, 9):
        assert f"\n{number}. " in out
    assert "fine-grained token" in out
    assert "ruleset" in out
    assert "web/.claude/project-instructions.md" in out
    assert "bash ops/install-launchd.sh" in out
    assert "ntfy" in out and "shop-test" in out
    assert "2 to 3" in out
    assert out.index("\n1. ") < out.index("\n8. ")


def test_the_real_home_is_not_touched(run: Run, home: Path) -> None:
    real = Path(os.path.expanduser("~"))
    assert real == home

    run("--no-labels")

    assert not (home / ".reviewradar").exists()
