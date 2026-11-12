"""ops/rollback.py returns the live site to the previous release (AC1 to AC6, rows M16 to M23).

Run: uv run pytest -q --no-cov ops/tests/test_rollback.py
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from ops import flow_config, live_check, release, rollback
from ops.tests.test_release import git, merge_pr, repo  # noqa: F401
from ops.tests.test_release_client_facing import merge_pr_file

KEY = "rnd_secret_key_value"
SERVICE = "srv-123"
FIRST, SECOND, THIRD = "v2026.11.10", "v2026.11.11", "v2026.11.12"
MIGRATIONS = (
    "reviews/migrations/0006_replytemplate.py",
    "reviews/migrations/0007_reviewfollowup.py",
)
TWO_MIGRATIONS = (
    "Migrations since v2026.11.10: 2 "
    "(the live database is rebuilt from demo data at start; nothing to reverse)"
)


class FakeRender:
    """Records every call; answers GET with a deploy list and POST with 202."""

    def __init__(
        self,
        deploys: list[tuple[str, str, str, str]] | None = None,
        get_status: int | None = 200,
        post_status: int | None = 202,
    ) -> None:
        self.deploys = deploys or []
        self.get_status = get_status
        self.post_status = post_status
        self.calls: list[tuple[str, str, dict[str, str], bytes | None, float]] = []

    def __call__(
        self, method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float
    ) -> tuple[int | None, bytes]:
        self.calls.append((method, url, headers, body, timeout))
        if method == "GET":
            items = [
                {
                    "deploy": {
                        "id": deploy_id,
                        "status": status,
                        "commit": {"id": commit},
                        "createdAt": created,
                    },
                    "cursor": "c" + deploy_id,
                }
                for deploy_id, status, commit, created in self.deploys
            ]
            return self.get_status, json.dumps(items).encode()
        return self.post_status, b"{}"

    def methods(self) -> list[str]:
        return [call[0] for call in self.calls]


class World:
    def __init__(self, origin: Path, clone: Path, shas: list[str]) -> None:
        self.origin = origin
        self.clone = clone
        self.shas = shas


def build_with_two_migrations(
    repo_paths: tuple[Path, Path],
    tags: Mapping[int, list[str]],
    deploy_at: int | None = 2,
) -> World:
    """Three merged pull requests (the second adds two migrations); tags by commit index."""
    origin, clone = repo_paths
    shas: list[str] = [merge_pr(clone, 1, "Add first thing")]
    app_dir = flow_config.load().project_app_dir
    git(clone, "switch", "-c", "feat/2")
    for relative in MIGRATIONS:
        target = clone / app_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# migration")
    git(clone, "add", ".")
    git(clone, "commit", "-m", "work 2")
    git(clone, "switch", "main")
    git(
        clone,
        "merge",
        "--no-ff",
        "feat/2",
        "-m",
        "Merge pull request #2 from owner/feat/2",
        "-m",
        "Add reply templates",
    )
    git(clone, "push", "origin", "main")
    shas.append(git(clone, "rev-parse", "HEAD"))
    shas.append(merge_pr(clone, 3, "Add third thing"))
    for index, sha in enumerate(shas):
        for tag in tags.get(index, []):
            git(clone, "tag", tag, sha)
            git(clone, "push", "origin", tag)
    if deploy_at is not None:
        git(clone, "push", "origin", f"{shas[deploy_at]}:refs/heads/deploy")
    return World(origin, clone, shas)


DEFAULT_TAGS: dict[int, list[str]] = {0: [FIRST], 1: [SECOND], 2: [THIRD]}


@pytest.fixture(autouse=True)
def no_real_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(live_check, "REPO_ENV", tmp_path / "missing" / "agent.env")


@pytest.fixture
def world(repo: tuple[Path, Path]) -> World:  # noqa: F811
    return build_with_two_migrations(repo, DEFAULT_TAGS)


def environ(tmp_path: Path, **overrides: str) -> dict[str, str]:
    home = tmp_path / "flow_home"
    home.mkdir(exist_ok=True)
    values = {"RENDER_API_KEY": KEY, "RENDER_SERVICE_ID": SERVICE, "FLOW_HOME": str(home)}
    values.update(overrides)
    return values


def deploys_for(world: World, tag_index: int = 1) -> FakeRender:
    return FakeRender(
        [
            ("dep-other", "live", world.shas[2], "2026-11-12T08:00:00Z"),
            ("dep-target", "deactivated", world.shas[tag_index], "2026-11-11T08:00:00Z"),
        ]
    )


def config_with(tmp_path: Path, persistent: bool) -> Path:
    text = flow_config.DEFAULT_PATH.read_text()
    changed = text.replace(
        "persistent_database = false",
        "persistent_database = " + ("true" if persistent else "false"),
    )
    path = tmp_path / "flow.toml"
    path.write_text(changed)
    return path


def run(
    world: World,
    tmp_path: Path,
    fake: FakeRender,
    *args: str,
    persistent: bool = False,
    **env: str,
) -> int:
    return rollback.main(
        list(args),
        request=fake,
        environ=environ(tmp_path, **env),
        cwd=world.clone,
        config_path=config_with(tmp_path, persistent),
    )


def assert_refused(
    code: int, fake: FakeRender, capsys: pytest.CaptureFixture[str], line: str
) -> None:
    out, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == [line]
    assert out == ""
    assert fake.calls == []


def roll_back_line(out: str) -> str:
    return next(ln for ln in out.splitlines() if ln.startswith("Roll back to:"))


# M16 -----------------------------------------------------------------------------------------


def test_m16_target_is_the_newest_release_before_the_current_one(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run(world, tmp_path, deploys_for(world), "--dry-run")
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert lines[0] == f"Current: {THIRD} {world.shas[2][:7]}"
    assert roll_back_line("\n".join(lines)).startswith(
        f"Roll back to: {SECOND} {world.shas[1][:7]}"
    )


def test_m16_to_option_picks_the_named_older_release(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender([("dep-first", "deactivated", world.shas[0], "2026-11-10T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run", "--to", FIRST)
    out = capsys.readouterr().out
    assert code == 0
    assert roll_back_line(out).startswith(f"Roll back to: {FIRST} {world.shas[0][:7]}")


def test_m16_release_with_a_counter_sorts_after_the_plain_date(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world = build_with_two_migrations(repo, {0: [FIRST], 1: [THIRD], 2: [THIRD + ".2"]})
    fake = FakeRender([("dep-mid", "live", world.shas[1], "2026-11-12T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run")
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert lines[0] == f"Current: {THIRD}.2 {world.shas[2][:7]}"
    assert roll_back_line("\n".join(lines)).startswith(f"Roll back to: {THIRD} ")


def test_m16_counter_is_compared_as_a_number(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tags = {0: [FIRST], 1: [THIRD + ".2"], 2: [THIRD + ".10"]}
    world = build_with_two_migrations(repo, tags)
    fake = FakeRender([("dep-mid", "live", world.shas[1], "2026-11-12T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run")
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert lines[0] == f"Current: {THIRD}.10 {world.shas[2][:7]}"
    assert roll_back_line("\n".join(lines)).startswith(f"Roll back to: {THIRD}.2 ")


def test_m16_tags_on_the_current_commit_are_skipped_as_target(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world = build_with_two_migrations(repo, {0: [FIRST], 1: [SECOND], 2: [THIRD, THIRD + ".2"]})
    fake = FakeRender([("dep-mid", "live", world.shas[1], "2026-11-11T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run")
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert lines[0] == f"Current: {THIRD}.2 {world.shas[2][:7]}"
    assert roll_back_line("\n".join(lines)).startswith(f"Roll back to: {SECOND} ")


# M17 -----------------------------------------------------------------------------------------


def test_m17_one_release_only_has_no_earlier_release(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world = build_with_two_migrations(repo, {2: [THIRD]})
    fake = FakeRender()
    code = run(world, tmp_path, fake, "--dry-run")
    assert_refused(code, fake, capsys, "no earlier release to roll back to")


def test_m17_deploy_not_on_a_release_tag_is_refused(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world = build_with_two_migrations(repo, {0: [FIRST], 1: [SECOND]}, deploy_at=2)
    fake = FakeRender()
    code = run(world, tmp_path, fake, "--dry-run")
    assert_refused(code, fake, capsys, "origin/deploy is not a release tag")


def test_m17_to_a_tag_that_does_not_exist_is_not_an_earlier_release(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender()
    code = run(world, tmp_path, fake, "--dry-run", "--to", "v2026.12.01")
    assert_refused(code, fake, capsys, "v2026.12.01 is not an earlier release")


def test_m17_to_a_tag_on_the_commit_of_deploy_is_not_an_earlier_release(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world = build_with_two_migrations(repo, {0: [FIRST], 1: [SECOND], 2: [THIRD, "v2026.11.09"]})
    fake = FakeRender()
    code = run(world, tmp_path, fake, "--dry-run", "--to", "v2026.11.09")
    assert_refused(code, fake, capsys, "v2026.11.09 is not an earlier release")


def test_m17_blank_api_key_is_refused_with_its_name(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender()
    code = run(world, tmp_path, fake, "--dry-run", RENDER_API_KEY="")
    assert_refused(code, fake, capsys, "RENDER_API_KEY is not set in agent.env")


def test_m17_blank_service_id_is_refused_with_its_name(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender()
    code = run(world, tmp_path, fake, "--dry-run", RENDER_SERVICE_ID="")
    assert_refused(code, fake, capsys, "RENDER_SERVICE_ID is not set in agent.env")


# M18 -----------------------------------------------------------------------------------------


def test_m18_newest_deploy_of_the_target_commit_is_chosen(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender(
        [
            ("dep-live-old", "live", world.shas[1], "2026-11-11T08:00:00Z"),
            ("dep-deactivated-new", "deactivated", world.shas[1], "2026-11-11T20:00:00Z"),
            ("dep-other", "live", world.shas[2], "2026-11-12T08:00:00Z"),
        ]
    )
    code = run(world, tmp_path, fake, "--dry-run")
    out = capsys.readouterr().out
    assert code == 0
    assert "Render deploy: dep-deactivated-new" in out.splitlines()
    assert fake.methods() == ["GET"]
    method, url, headers, _, timeout = fake.calls[0]
    assert url == f"{rollback.RENDER_API}/services/{SERVICE}/deploys?limit=100"
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert headers["Accept"] == "application/json"
    assert timeout == 30


# M19 -----------------------------------------------------------------------------------------


def test_m19_no_deploy_of_the_target_is_refused(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender([("dep-other", "live", world.shas[2], "2026-11-12T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run")
    out, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == [f"no Render deploy of {SECOND} ({world.shas[1][:7]}) found"]
    assert out == ""
    assert fake.methods() == ["GET"]


def test_m19_deploy_that_failed_is_not_a_rollback_target(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender([("dep-bad", "build_failed", world.shas[1], "2026-11-11T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run")
    _, err = capsys.readouterr()
    assert code == 1
    assert err.strip() == f"no Render deploy of {SECOND} ({world.shas[1][:7]}) found"


def test_m19_http_401_is_reported_and_the_key_is_never_printed(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender(get_status=401)
    code = run(world, tmp_path, fake, "--dry-run")
    out, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == ["Render API failed: HTTP 401"]
    assert KEY not in out + err


def test_m19_no_answer_is_reported(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender(get_status=None)
    code = run(world, tmp_path, fake, "--dry-run")
    out, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == ["Render API failed: no answer"]
    assert KEY not in out + err


def test_m18_dates_with_and_without_an_offset_compare_as_utc(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender(
        [
            ("dep-aware-old", "live", world.shas[1], "2026-11-11T08:00:00Z"),
            ("dep-naive-new", "deactivated", world.shas[1], "2026-11-11T20:00:00"),
        ]
    )
    code = run(world, tmp_path, fake, "--dry-run")
    assert code == 0
    assert "Render deploy: dep-naive-new" in capsys.readouterr().out.splitlines()


def test_m17_git_that_cannot_start_is_one_line(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender()
    code = rollback.main(
        ["--dry-run"],
        request=fake,
        environ=environ(tmp_path),
        cwd=tmp_path / "missing-folder",
        config_path=config_with(tmp_path, False),
    )
    out, err = capsys.readouterr()
    assert code == 1
    assert err.startswith("git fetch origin --tags failed: ")
    assert len(err.strip().splitlines()) == 1
    assert out == ""
    assert fake.calls == []


def test_m19_a_redirect_is_not_followed() -> None:
    handlers: list[Any] = getattr(rollback._OPENER, "handlers", [])
    assert any(isinstance(handler, rollback._NoRedirect) for handler in handlers)


# M20 -----------------------------------------------------------------------------------------


def test_m20_two_migrations_are_listed_when_the_database_is_rebuilt(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender([("dep-first", "deactivated", world.shas[0], "2026-11-10T08:00:00Z")])
    code = run(world, tmp_path, fake, "--dry-run", "--to", FIRST, persistent=False)
    out = capsys.readouterr().out
    assert code == 0
    assert TWO_MIGRATIONS in out.splitlines()


# M21 -----------------------------------------------------------------------------------------


def test_m21_persistent_database_with_migrations_is_refused(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRender([("dep-first", "deactivated", world.shas[0], "2026-11-10T08:00:00Z")])
    code = run(world, tmp_path, fake, "--to", FIRST, persistent=True)
    out, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == [
        "2 migrations since v2026.11.10 and the database is persistent: "
        "write a reversing migration on main and release it"
    ]
    assert out == ""
    assert "POST" not in fake.methods()


def test_m21_persistent_database_without_migrations_goes_on(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run(world, tmp_path, deploys_for(world), "--dry-run", persistent=True)
    out = capsys.readouterr().out
    assert code == 0
    assert f"Migrations since {SECOND}: 0" in out.splitlines()


def test_m21_one_migration_uses_the_singular_form(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin, clone = repo
    shas = [merge_pr(clone, 1, "Add first thing")]
    shas.append(merge_pr_file(clone, 2, "Add reply templates", MIGRATIONS[0]))
    shas.append(merge_pr(clone, 3, "Add third thing"))
    git(clone, "tag", FIRST, shas[0])
    git(clone, "tag", THIRD, shas[2])
    git(clone, "push", "origin", FIRST, THIRD)
    git(clone, "push", "origin", f"{shas[2]}:refs/heads/deploy")
    fake = FakeRender([("dep-first", "deactivated", shas[0], "2026-11-10T08:00:00Z")])
    code = rollback.main(
        ["--to", FIRST],
        request=fake,
        environ=environ(tmp_path),
        cwd=clone,
        config_path=config_with(tmp_path, True),
    )
    _, err = capsys.readouterr()
    assert code == 1
    assert err.strip() == (
        "1 migration since v2026.11.10 and the database is persistent: "
        "write a reversing migration on main and release it"
    )


# M22 -----------------------------------------------------------------------------------------


def expected_plan(world: World) -> list[str]:
    client, internal = release.merged_pull_requests(world.clone, world.shas[1], world.shas[2])
    undone = ["  " + line for line in (*client, *internal)] or ["  (none)"]
    subject = git(world.clone, "log", "-1", "--format=%s", world.shas[1])
    return [
        f"Current: {THIRD} {world.shas[2][:7]}",
        f"Roll back to: {SECOND} {world.shas[1][:7]} {subject}",
        "Render deploy: dep-target",
        f"Migrations since {SECOND}: 0",
        "Pull requests undone:",
        *undone,
    ]


def test_m22_dry_run_prints_the_plan_in_order_and_sends_no_post(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = deploys_for(world)
    code = run(world, tmp_path, fake, "--dry-run")
    out = capsys.readouterr().out
    assert code == 0
    assert out.splitlines() == expected_plan(world)
    assert "#3 Add third thing" in out
    assert fake.methods() == ["GET"]


def test_m22_real_run_posts_the_rollback_and_ends_with_the_check_command(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = deploys_for(world)
    code = run(world, tmp_path, fake)
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert lines[:-1] == expected_plan(world)
    assert lines[-1] == (
        f"Rollback started. Check it with: uv run python ops/live_check.py --commit {world.shas[1]}"
    )
    assert fake.methods() == ["GET", "POST"]
    method, url, headers, body, timeout = fake.calls[1]
    assert url == f"{rollback.RENDER_API}/services/{SERVICE}/rollback"
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"
    assert body is not None
    assert json.loads(body) == {"deployId": "dep-target"}
    assert timeout == 30


def test_m22_post_failure_is_reported(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = deploys_for(world)
    fake.post_status = 500
    code = run(world, tmp_path, fake)
    _, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == ["Render API failed: HTTP 500"]


def test_m22_post_without_answer_is_reported(
    world: World, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = deploys_for(world)
    fake.post_status = None
    code = run(world, tmp_path, fake)
    _, err = capsys.readouterr()
    assert code == 1
    assert err.strip().splitlines() == ["Render API failed: no answer"]


# M23 -----------------------------------------------------------------------------------------


def refs(path: Path) -> str:
    return git(path, "for-each-ref", "--format=%(refname) %(objectname)")


def test_m23_a_real_run_moves_no_branch_or_tag_and_pushes_nothing(
    world: World, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git(world.clone, "fetch", "origin", "--tags")
    origin_before, clone_before = refs(world.origin), refs(world.clone)
    ran: list[list[str]] = []
    real_run = subprocess.run

    def spy(command: Any, *args: Any, **kwargs: Any) -> Any:
        ran.append([str(part) for part in command])
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    fake = deploys_for(world)
    code = run(world, tmp_path, fake)
    monkeypatch.undo()
    assert code == 0
    assert refs(world.origin) == origin_before
    assert refs(world.clone) == clone_before
    assert not any("push" in command for command in ran)
    assert fake.methods() == ["GET", "POST"]
