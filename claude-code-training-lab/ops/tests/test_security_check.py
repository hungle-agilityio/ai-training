"""ops/security_check.py runs three security checks on the exact release commit (AC1 to AC5).

Every command is answered by a fake subprocess.run: never a real uv, uvx or network.
Run: uv run pytest -q --no-cov ops/tests/test_security_check.py
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ops import flow_config, release, security_check
from ops.tests.test_release import merge_pr, repo  # noqa: F401

SHA = "a" * 40
SINCE = "b" * 40
APP_DIR = flow_config.load().project_app_dir
NAMES = ("deploy settings", "dependencies", "secrets")
GITHUB_TOKEN = "ghp_" + "a" * 36  # built at run time: no token is written in this file
ANTHROPIC_KEY = "sk-ant-" + "b" * 30
OK_AUDIT = json.dumps({"dependencies": [{"name": "django", "version": "5.0", "vulns": []}]})
W004 = "?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting."


def key_of(args: Sequence[str]) -> str:
    """Name the kind of command the code asked for."""
    if args[0] == "git":
        if "worktree" in args:
            return "worktree-add" if "add" in args else "worktree-remove"
        return "diff" if "diff" in args else "ls-tree"
    if args[0] == "uvx":
        return "audit"
    return "export" if "export" in args else "deploy"


class Fake:
    """Answers each command; every call is recorded as (key, args, kwargs)."""

    def __init__(self) -> None:
        self.answers: dict[str, subprocess.CompletedProcess[str] | BaseException] = {}
        self.calls: list[tuple[str, list[str], dict[str, Any]]] = []
        self.files: dict[str, bytes] = {}
        self.with_manage = True
        self.with_lock = True
        self.tree: Path | None = None

    def answer(self, key: str, code: int = 0, out: str = "", err: str = "") -> None:
        self.answers[key] = subprocess.CompletedProcess([key], code, out, err)

    def fail(self, key: str, error: BaseException) -> None:
        self.answers[key] = error

    def keys(self) -> list[str]:
        return [key for key, _, _ in self.calls]

    def args_of(self, key: str) -> list[str]:
        return next(args for k, args, _ in self.calls if k == key)

    def kwargs_of(self, key: str) -> dict[str, Any]:
        return next(kwargs for k, _, kwargs in self.calls if k == key)

    def build_tree(self, args: list[str]) -> None:
        self.tree = Path(args[args.index("--detach") + 1])
        app = self.tree if APP_DIR == "." else self.tree / APP_DIR
        app.mkdir(parents=True)
        if self.with_manage:
            (app / "manage.py").write_text("")
        if self.with_lock:
            (app / "uv.lock").write_text("")
        for name, data in self.files.items():
            target = self.tree / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

    def __call__(self, args: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        key = key_of(args)
        self.calls.append((key, list(args), kwargs))
        answer = self.answers.get(key)
        if key == "worktree-add" and not isinstance(answer, BaseException):
            self.build_tree(list(args))
        if isinstance(answer, BaseException):
            raise answer
        if answer is not None:
            return answer
        if key == "audit":
            return subprocess.CompletedProcess(args, 0, OK_AUDIT, "")
        if key == "ls-tree":
            return subprocess.CompletedProcess(args, 0, "\n".join(self.files), "")
        return subprocess.CompletedProcess(args, 0, "", "")


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> Fake:
    stand_in = Fake()
    monkeypatch.setattr(subprocess, "run", stand_in)
    return stand_in


def run_checks(since: str | None = SINCE, cwd: Path = Path("/app")) -> dict[str, Any]:
    results = security_check.run_checks(SHA, since, cwd)
    return {result.name: result for result in results}


def diff_adding(path: str, *added: tuple[int, str]) -> str:
    """A zero-context git diff that adds each (line number, text) in its own hunk."""
    lines = [f"diff --git a/{path} b/{path}", "--- /dev/null", f"+++ b/{path}"]
    for number, text in added:
        lines += [f"@@ -0,0 +{number},1 @@", "+" + text]
    return "\n".join(lines) + "\n"


# M14 (AC1)


def test_all_commands_answering_zero_give_three_ok_results_in_order(fake: Fake) -> None:
    results = security_check.run_checks(SHA, SINCE, Path("/app"))
    assert tuple(result.name for result in results) == NAMES
    assert all(result.ok for result in results)
    assert fake.keys()[0] == "worktree-add"
    assert fake.keys()[-1] == "worktree-remove"
    assert fake.keys().index("deploy") < fake.keys().index("export") < fake.keys().index("audit")
    assert fake.keys().index("audit") < fake.keys().index("diff")


def test_check_result_is_a_frozen_dataclass_with_name_ok_and_lines() -> None:
    result = security_check.CheckResult("secrets", True, ())
    assert (result.name, result.ok, result.lines) == ("secrets", True, ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.ok = False  # type: ignore[misc]


def test_worktree_is_added_detached_at_the_sha_from_cwd_and_removed_without_check(
    fake: Fake,
) -> None:
    cwd = Path("/somewhere/app")
    security_check.run_checks(SHA, SINCE, cwd)
    add = fake.args_of("worktree-add")
    assert (
        add[-1] == SHA
        and "--detach" in add
        and add[add.index("--detach") + 1].endswith("release-tree")
    )
    assert fake.kwargs_of("worktree-add")["cwd"] == cwd
    assert fake.kwargs_of("worktree-add")["check"] is True
    remove = fake.args_of("worktree-remove")
    assert "--force" in remove and remove[-1] == add[add.index("--detach") + 1]
    assert fake.kwargs_of("worktree-remove")["check"] is False


def test_every_command_captures_text_with_replace_errors_and_a_timeout(fake: Fake) -> None:
    security_check.run_checks(SHA, SINCE, Path("/app"))
    assert len(fake.calls) >= 6
    for _, _, kwargs in fake.calls:
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["errors"] == "replace"
        assert kwargs["timeout"] == 300


def test_git_commands_turn_off_quote_path(fake: Fake) -> None:
    security_check.run_checks(SHA, SINCE, Path("/app"))
    for key in ("worktree-add", "worktree-remove", "diff"):
        args = fake.args_of(key)
        assert args[args.index("-c") + 1] == "core.quotePath=false"


def test_deploy_check_runs_in_the_worktree_app_folder_with_a_production_environment(
    fake: Fake,
) -> None:
    security_check.run_checks(SHA, SINCE, Path("/app"))
    assert fake.args_of("deploy") == [
        "uv",
        "run",
        "--frozen",
        "python",
        "manage.py",
        "check",
        "--deploy",
        "--fail-level",
        "WARNING",
    ]
    assert fake.tree is not None
    expected = fake.tree if APP_DIR == "." else fake.tree / APP_DIR
    kwargs = fake.kwargs_of("deploy")
    assert Path(kwargs["cwd"]) == expected
    env = kwargs["env"]
    assert env["DJANGO_DEBUG"] == "0"
    assert env["DJANGO_ALLOWED_HOSTS"] == "reviewradar.onrender.com"
    assert security_check.DEPLOY_HOST == "reviewradar.onrender.com"
    assert len(env["DJANGO_SECRET_KEY"]) >= 50


def test_audit_runs_pinned_pip_audit_on_the_exported_requirements(fake: Fake) -> None:
    security_check.run_checks(SHA, SINCE, Path("/app"))
    export = fake.args_of("export")
    assert export[:2] == ["uv", "export"]
    for flag in ("--frozen", "--no-dev", "--no-hashes", "--no-emit-project", "-o"):
        assert flag in export
    requirements = export[export.index("-o") + 1]
    audit = fake.args_of("audit")
    assert audit[0] == "uvx" and audit[1] == "pip-audit==2.10.1"
    assert audit[audit.index("-r") + 1] == requirements
    for flag in ("--no-deps", "--disable-pip", "--format"):
        assert flag in audit
    assert audit[audit.index("--format") + 1] == "json"


def test_no_manage_py_skips_the_deploy_check_as_ok(fake: Fake) -> None:
    fake.with_manage = False
    result = run_checks()["deploy settings"]
    assert result.ok and result.lines == ("skipped: no manage.py",)
    assert "deploy" not in fake.keys()


def test_no_uv_lock_skips_the_dependency_check_as_ok(fake: Fake) -> None:
    fake.with_lock = False
    result = run_checks()["dependencies"]
    assert result.ok and result.lines == ("skipped: no uv.lock",)
    assert "export" not in fake.keys() and "audit" not in fake.keys()


# M15 (AC2)


def test_deploy_check_failure_lists_the_security_lines_of_stdout_and_stderr(fake: Fake) -> None:
    other = "?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True."
    fake.answer(
        "deploy", 1, out="System check identified issues:\n" + W004 + "\n", err=other + "\n"
    )
    result = run_checks()["deploy settings"]
    assert not result.ok
    assert set(result.lines) == {W004, other}
    assert all("(security." in line for line in result.lines)


def test_deploy_check_failure_without_security_line_gives_last_non_empty_stderr_line(
    fake: Fake,
) -> None:
    fake.answer("deploy", 1, out="noise\n", err="Traceback\nImportError: no module named x\n\n")
    result = run_checks()["deploy settings"]
    assert not result.ok
    assert result.lines == ("ImportError: no module named x",)


# M16 (AC3)


def test_pip_audit_exit_one_with_a_vulnerability_gives_name_version_and_id(fake: Fake) -> None:
    report = {
        "dependencies": [
            {"name": "django", "version": "4.2.0", "vulns": [{"id": "PYSEC-2024-1"}]},
            {"name": "clean", "version": "1.0", "vulns": []},
            {"name": "local", "skip_reason": "not on PyPI"},
        ]
    }
    fake.answer("audit", 1, out=json.dumps(report))
    result = run_checks()["dependencies"]
    assert not result.ok
    assert result.lines == ("django 4.2.0 PYSEC-2024-1",)


def test_pip_audit_gives_one_line_per_vulnerability_of_each_dependency(fake: Fake) -> None:
    report = {
        "dependencies": [
            {"name": "a", "version": "1", "vulns": [{"id": "X-1"}, {"id": "X-2"}]},
            {"name": "b", "version": "2", "vulns": [{"id": "Y-1"}]},
        ]
    }
    fake.answer("audit", 1, out=json.dumps(report))
    assert run_checks()["dependencies"].lines == ("a 1 X-1", "a 1 X-2", "b 2 Y-1")


def test_pip_audit_exit_one_without_json_could_not_run(fake: Fake) -> None:
    fake.answer("audit", 1, out="", err="ConnectionError: no network")
    result = run_checks()["dependencies"]
    assert not result.ok
    assert result.lines == ("could not run: pip-audit exited 1",)


def test_uv_export_failing_means_dependencies_could_not_run(fake: Fake) -> None:
    fake.answer("export", 2, err="error")
    result = run_checks()["dependencies"]
    assert not result.ok
    assert result.lines == ("could not run: uv exited 2",)
    assert "audit" not in fake.keys()


# M17 (AC4)


def test_added_github_token_is_reported_by_path_and_line_and_never_by_text(fake: Fake) -> None:
    path = "claude-code-training-lab/reviews/token_sample.py"
    fake.answer("diff", 0, out=diff_adding(path, (3, 'TOKEN = "' + GITHUB_TOKEN + '"')))
    result = run_checks()["secrets"]
    assert not result.ok
    assert result.lines == (path + ":3",)
    assert GITHUB_TOKEN not in "".join(result.lines)
    assert "ghp_" not in "".join(result.lines)


def test_line_numbers_come_from_the_hunk_header_of_each_hunk(fake: Fake) -> None:
    path = "x/y.py"
    diff = (
        f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
        "@@ -1,2 +1,3 @@\n+harmless\n+harmless too\n"
        f"+K = '{GITHUB_TOKEN}'\n"
        "@@ -40 +50,2 @@\n+fine\n"
        f"+L = '{GITHUB_TOKEN}'\n"
    )
    fake.answer("diff", 0, out=diff)
    assert run_checks()["secrets"].lines == (path + ":3", path + ":51")


def test_added_anthropic_key_is_found(fake: Fake) -> None:
    fake.answer("diff", 0, out=diff_adding("conf/keys.py", (7, "KEY = '" + ANTHROPIC_KEY + "'")))
    result = run_checks()["secrets"]
    assert not result.ok
    assert result.lines == ("conf/keys.py:7",)
    assert "sk-ant" not in "".join(result.lines)


def test_removed_and_context_lines_and_header_lines_are_not_scanned(fake: Fake) -> None:
    diff = (
        "diff --git a/f.py b/f.py\n--- a/f.py\n"
        f"+++ b/f.py {GITHUB_TOKEN}\n"
        "@@ -1,2 +1,1 @@\n"
        f"-OLD = '{GITHUB_TOKEN}'\n"
        "+fine = 1\n"
    )
    fake.answer("diff", 0, out=diff)
    result = run_checks()["secrets"]
    assert result.ok and result.lines == ()


def test_secrets_diff_runs_between_since_and_sha_from_the_worktree_root(fake: Fake) -> None:
    run_checks(since=SINCE)
    args = fake.args_of("diff")
    assert args[-2:] == [SINCE, SHA]
    for flag in ("--no-color", "--no-ext-diff", "--no-relative", "--no-renames", "--unified=0"):
        assert flag in args
    assert fake.tree is not None
    assert Path(args[args.index("-C") + 1]) == fake.tree
    assert "ls-tree" not in fake.keys()


def test_first_release_scans_every_tracked_file_from_the_repository_root(fake: Fake) -> None:
    fake.files = {
        "README.md": b"nothing here\n",
        "claude-code-training-lab/reviews/token_sample.py": (
            b"a = 1\nb = 2\nTOKEN = '" + GITHUB_TOKEN.encode() + b"'\n"
        ),
        "top/key.txt": ANTHROPIC_KEY.encode() + b"\n",
    }
    result = run_checks(since=None)["secrets"]
    assert not result.ok
    assert set(result.lines) == {
        "claude-code-training-lab/reviews/token_sample.py:3",
        "top/key.txt:1",
    }
    args = fake.args_of("ls-tree")
    assert args[-1] == SHA
    for flag in ("-r", "--full-tree", "--name-only"):
        assert flag in args
    assert "diff" not in fake.keys()


def test_first_release_skips_files_that_are_not_utf8_text_or_cannot_be_opened(fake: Fake) -> None:
    fake.files = {
        "image.bin": b"\xff\xfe\x00" + GITHUB_TOKEN.encode(),
        "clean.txt": b"fine\n",
    }
    fake.answer("ls-tree", 0, out="image.bin\nclean.txt\nmissing.txt\n")
    result = run_checks(since=None)["secrets"]
    assert result.ok and result.lines == ()


def test_clean_added_lines_give_an_ok_secrets_check(fake: Fake) -> None:
    fake.answer("diff", 0, out=diff_adding("a.py", (1, "x = 1")))
    assert run_checks()["secrets"].ok


# M18 (AC5)


@pytest.mark.parametrize("key", ["deploy", "export", "audit"])
@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (FileNotFoundError("uv"), "FileNotFoundError"),
        (PermissionError("uv"), "PermissionError"),
        (subprocess.TimeoutExpired(["uv"], 300), "TimeoutExpired"),
    ],
)
def test_a_command_that_cannot_run_gives_could_not_run_with_the_exception_name(
    fake: Fake, key: str, error: BaseException, reason: str
) -> None:
    fake.fail(key, error)
    results = run_checks()
    failed = results["dependencies" if key != "deploy" else "deploy settings"]
    assert not failed.ok
    assert failed.lines == ("could not run: " + reason,)
    others = [r for name, r in results.items() if r is not failed]
    assert len(others) == 2 and all(r.ok for r in others)
    assert fake.keys()[-1] == "worktree-remove"


def test_git_diff_failing_means_secrets_could_not_run_and_other_checks_still_run(
    fake: Fake,
) -> None:
    fake.fail("diff", subprocess.CalledProcessError(128, ["git", "diff"], stderr="fatal"))
    results = run_checks()
    assert not results["secrets"].ok
    assert results["secrets"].lines == ("could not run: git exited 128",)
    assert results["deploy settings"].ok and results["dependencies"].ok
    assert fake.keys()[-1] == "worktree-remove"


def test_git_ls_tree_failing_means_secrets_could_not_run(fake: Fake) -> None:
    fake.fail("ls-tree", subprocess.CalledProcessError(128, ["git", "ls-tree"]))
    result = run_checks(since=None)["secrets"]
    assert not result.ok
    assert result.lines == ("could not run: git exited 128",)


def test_pip_audit_exit_two_could_not_run(fake: Fake) -> None:
    fake.answer("audit", 2, err="usage error")
    result = run_checks()["dependencies"]
    assert not result.ok
    assert result.lines == ("could not run: pip-audit exited 2",)


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, ["git", "worktree", "remove"]),
        subprocess.TimeoutExpired(["git"], 300),
        OSError("gone"),
    ],
)
def test_a_worktree_remove_that_raises_does_not_change_the_results(
    fake: Fake, error: BaseException
) -> None:
    fake.fail("worktree-remove", error)
    results = security_check.run_checks(SHA, SINCE, Path("/app"))
    assert tuple(result.name for result in results) == NAMES
    assert all(result.ok for result in results)


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(128, ["git", "worktree", "add"], stderr="fatal: bad"),
        subprocess.TimeoutExpired(["git"], 300),
        FileNotFoundError("git"),
    ],
)
def test_a_failing_worktree_add_leaves_run_checks_and_no_check_runs(
    fake: Fake, error: BaseException
) -> None:
    fake.fail("worktree-add", error)
    with pytest.raises(type(error)):
        security_check.run_checks(SHA, SINCE, Path("/app"))
    assert fake.keys() == ["worktree-add"]


def test_an_oserror_making_the_temporary_directory_acts_like_a_failed_worktree_add(
    fake: Fake, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(tempfile, "TemporaryDirectory", broken)
    monkeypatch.setattr(tempfile, "mkdtemp", broken)
    with pytest.raises(OSError):
        security_check.run_checks(SHA, SINCE, Path("/app"))
    assert "deploy" not in fake.keys()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (subprocess.CalledProcessError(128, ["git"], stderr="fatal: no such commit"), "fatal"),
        (subprocess.TimeoutExpired(["git"], 300), "TimeoutExpired"),
        (FileNotFoundError("git"), "FileNotFoundError"),
    ],
)
def test_release_main_exits_one_with_git_or_gh_failed_when_the_worktree_add_fails(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: BaseException,
    expected: str,
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "Add the filter")
    real = subprocess.run

    def only_worktree_add_fails(args: Sequence[str], **kwargs: Any) -> Any:
        if "worktree" in args and "add" in args:
            raise error
        return real(args, **kwargs)

    monkeypatch.setattr(release, "latest_checks", lambda sha, cwd: "success")
    monkeypatch.setattr(subprocess, "run", only_worktree_add_fails)
    at = datetime(2026, 10, 30, 18, 30, tzinfo=UTC)
    assert release.main(["--dry-run"], cwd=clone, now=at) == 1
    err = capsys.readouterr().err
    assert err.startswith("git or gh failed:")
    assert expected in err


# Added during build

HOOK = Path(__file__).resolve().parents[3] / "plugins/agent-flow/hooks/before-commit-check.py"


def test_secret_pattern_is_the_commit_hook_pattern_plus_the_anthropic_key() -> None:
    spec = importlib.util.spec_from_file_location("commit_hook", HOOK)
    assert spec is not None and spec.loader is not None
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    expected = hook.SECRET.pattern + r"|sk-ant-[A-Za-z0-9_-]{20,}"
    assert security_check.SECRET_PATTERN.pattern == expected


def test_added_lines_follows_hunks_deleted_files_plus_plus_content_and_tabs() -> None:
    diff = (
        "diff --git a/one.py b/one.py\n--- a/one.py\n+++ b/one.py\n"
        "@@ -1 +1,2 @@\n-old\n+first\n+++second\n"
        "@@ -9 +10 @@\n-gone\n+tenth\n\\ No newline at end of file\n"
        "diff --git a/dead.py b/dead.py\n--- a/dead.py\n+++ /dev/null\n"
        "@@ -1 +0,0 @@\n-bye\n"
        "diff --git a/my file.py b/my file.py\n--- /dev/null\n+++ b/my file.py\t\n"
        "@@ -0,0 +1 @@\n+spaced\n"
    )
    assert list(security_check.added_lines(diff)) == [
        ("one.py", 1, "first"),
        ("one.py", 2, "++second"),
        ("one.py", 10, "tenth"),
        ("my file.py", 1, "spaced"),
    ]


def test_the_scratch_folder_is_gone_after_run_checks(fake: Fake) -> None:
    security_check.run_checks(SHA, SINCE, Path("/app"))
    assert fake.tree is not None
    assert not fake.tree.parent.exists()


def test_a_tracked_symlink_is_skipped_on_a_first_release(fake: Fake, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("K = '" + GITHUB_TOKEN + "'\n")
    original = fake.build_tree

    def with_link(args: list[str]) -> None:
        original(args)
        assert fake.tree is not None
        (fake.tree / "link.txt").symlink_to(outside)

    fake.build_tree = with_link  # type: ignore[method-assign]
    fake.answer("ls-tree", 0, out="link.txt\n")
    result = run_checks(since=None)["secrets"]
    assert result.ok and result.lines == ()


def test_the_module_imports_when_started_from_the_ops_folder() -> None:
    ops = Path(security_check.__file__).resolve().parent
    code = f"import sys; sys.path.insert(0, {str(ops)!r}); import security_check"
    done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("separator", [" ", " ", "\x85", "\x0c", "\x1c", "\x0c+"])
def test_a_unicode_line_separator_inside_an_added_line_does_not_hide_a_token(
    fake: Fake, separator: str
) -> None:
    path = "x/sep.py"
    first = f"a = 1{separator}K = '{GITHUB_TOKEN}'"
    second = f"L = '{GITHUB_TOKEN}'"
    diff = (
        f"diff --git a/{path} b/{path}\n--- /dev/null\n+++ b/{path}\n"
        f"@@ -0,0 +1,2 @@\n+{first}\n+{second}\n"
    )
    fake.answer("diff", 0, out=diff)
    assert run_checks()["secrets"].lines == (path + ":1", path + ":2")


def test_a_tail_after_a_carriage_return_turned_into_a_newline_is_scanned() -> None:
    diff = (
        "diff --git a/x/cr.py b/x/cr.py\n--- /dev/null\n+++ b/x/cr.py\n"
        f"@@ -0,0 +7,1 @@\n+x = 1\nTOKEN = '{GITHUB_TOKEN}'\n"
    )
    found = [(p, n) for p, n, text in security_check.added_lines(diff) if "ghp_" in text]
    assert found == [("x/cr.py", 7)]


def test_a_carriage_return_tail_in_the_middle_keeps_the_next_added_line_number() -> None:
    diff = (
        "diff --git a/x/cr.py b/x/cr.py\n--- /dev/null\n+++ b/x/cr.py\n"
        f"@@ -0,0 +1,2 @@\n+x = 1\nTOKEN = '{GITHUB_TOKEN}'\n+y = 2\n"
    )
    found = [(p, n, "ghp_" in text) for p, n, text in security_check.added_lines(diff)]
    assert found == [("x/cr.py", 1, False), ("x/cr.py", 1, True), ("x/cr.py", 2, False)]


def test_a_tail_after_the_last_added_line_of_a_hunk_is_scanned_and_headers_still_work(
    fake: Fake,
) -> None:
    diff = (
        "diff --git a/one.py b/one.py\n--- /dev/null\n+++ b/one.py\n"
        f"@@ -0,0 +1,1 @@\n+x = 1\nTOKEN = '{GITHUB_TOKEN}'\n"
        "diff --git a/two.py b/two.py\nnew file mode 100644\nindex 0000000..1111111\n"
        "--- /dev/null\n+++ b/two.py\n"
        f"@@ -0,0 +3,1 @@\n+K = '{GITHUB_TOKEN}'\n"
    )
    fake.answer("diff", 0, out=diff)
    assert run_checks()["secrets"].lines == ("one.py:1", "two.py:3")


def test_a_carriage_return_tail_starting_with_a_minus_does_not_hide_the_rest() -> None:
    diff = (
        "diff --git a/x/cr.py b/x/cr.py\n--- /dev/null\n+++ b/x/cr.py\n"
        f"@@ -0,0 +1,2 @@\n+a\n-b\nK = '{GITHUB_TOKEN}'\n+- {GITHUB_TOKEN}\n"
    )
    found = [(p, n) for p, n, text in security_check.added_lines(diff) if "ghp_" in text]
    assert found == [("x/cr.py", 1), ("x/cr.py", 2)]


def test_a_carriage_return_tail_starting_with_a_plus_does_not_hide_the_next_added_line() -> None:
    diff = (
        "diff --git a/x/cr.py b/x/cr.py\n--- /dev/null\n+++ b/x/cr.py\n"
        f"@@ -0,0 +1,2 @@\n+a\n+b\n+K = '{GITHUB_TOKEN}'\n+++ b/{GITHUB_TOKEN}\n"
        "diff --git a/two.py b/two.py\n--- /dev/null\n+++ b/two.py\n"
        f"@@ -0,0 +1 @@\n+L = '{GITHUB_TOKEN}'\n"
    )
    found = [p for p, _, text in security_check.added_lines(diff) if "ghp_" in text]
    assert found == ["x/cr.py", "x/cr.py", "two.py"]


def test_first_release_line_numbers_count_newlines_only(fake: Fake) -> None:
    fake.files = {"notes.txt": ("a\x0cb\x1cc\nK = '" + GITHUB_TOKEN + "'\n").encode()}
    assert run_checks(since=None)["secrets"].lines == ("notes.txt:2",)
