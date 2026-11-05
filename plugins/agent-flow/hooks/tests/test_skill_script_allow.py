"""The plugin's skill scripts run without a prompt, and nothing else does.

Run: uv run pytest ../plugins/agent-flow/hooks/tests --no-cov -q (from the app folder)
"""

import json
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parents[1]
PLUGIN = HOOKS.parent
HOOK = HOOKS / "before-skill-script-allow.py"


def load() -> ModuleType:
    spec = util.spec_from_file_location("before_skill_script_allow", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ALLOW = load()
REPORT = PLUGIN / "skills" / "build-verify-report" / "build_report.py"
GATE = PLUGIN / "skills" / "share-report" / "share_gate.py"


def payload(command: str, cwd: Path = PLUGIN) -> dict[str, object]:
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}


@pytest.mark.parametrize(
    "command",
    [
        f"python3 -I {GATE} out/verify/20261105-1200",
        f"python3 {GATE} out/verify/x",
        f'uv run python {REPORT} --title "Hooks move (#222)" --no-ui --no-open',
        f"uv run python3 {REPORT} --no-open --title x",
        f"python3 -I '{GATE}' out/verify/x",
    ],
)
def test_a_plain_call_of_a_skill_script_is_allowed(command: str) -> None:
    assert ALLOW.decide(payload(command)) is not None


def test_a_relative_path_is_resolved_from_the_cwd() -> None:
    command = "python3 -I skills/share-report/share_gate.py out/verify/x"

    assert ALLOW.decide(payload(command, PLUGIN)) is not None
    assert ALLOW.decide(payload(command, PLUGIN / "hooks")) is None


def test_dot_dot_out_of_the_plugin_is_not_allowed(tmp_path: Path) -> None:
    outside = tmp_path / "skills" / "share-report" / "share_gate.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("print('escaped')\n")
    ups = "/".join([".."] * len(GATE.parent.parts))
    sneaky = f"{GATE.parent}/{ups}{outside}"
    assert Path(sneaky).resolve() == outside.resolve()

    assert ALLOW.decide(payload(f"python3 -I {sneaky} x")) is None


def test_a_link_to_a_script_outside_the_plugin_is_not_allowed(tmp_path: Path) -> None:
    outside = tmp_path / "evil.py"
    outside.write_text("print('escaped')\n")
    link = tmp_path / "plugin" / "skills" / "share-report" / "share_gate.py"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)

    assert ALLOW.decide(payload(f"python3 -I {link} x"), tmp_path / "plugin") is None


@pytest.mark.parametrize(
    "command",
    [
        f"python3 -I {GATE} x; rm -rf out",
        f"python3 -I {GATE} x && git push",
        f"python3 -I {GATE} x | tee log",
        f"python3 -I {GATE} x > /tmp/log",
        f"python3 -I {GATE} $(whoami)",
        f"python3 -I {GATE} `whoami`",
        f"python3 -I {GATE} $HOME",
        f"python3 -I {GATE} x\npython3 -I {GATE} y",
        f"FOO=1 python3 -I {GATE} x",
        f"python3 -c 'print(1)' {GATE}",
        f"python3 -m pytest {GATE}",
        f"bash {GATE}",
        f"uv run {GATE}",
        f"python3 -I {GATE.parent / 'tests' / 'test_share_gate.py'}",
        f"python3 -I {PLUGIN / 'hooks' / 'before-edit-check.py'}",
        f"python3 -I {GATE.parent / 'rules.md'}",
        f"python3 -I {GATE.parent / 'missing.py'}",
        "python3 -I",
        "",
        f"python3 -I {GATE} 'unclosed",
    ],
)
def test_anything_else_is_left_to_the_permission_rules(command: str) -> None:
    assert ALLOW.decide(payload(command)) is None


def test_other_tools_are_ignored() -> None:
    edit = {"tool_name": "Edit", "tool_input": {"file_path": str(GATE)}, "cwd": str(PLUGIN)}

    assert ALLOW.decide(edit) is None


def run_hook(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(HOOK)], input=body, capture_output=True, text=True, check=False
    )


def test_the_hook_answers_allow_with_the_documented_json() -> None:
    done = run_hook(json.dumps(payload(f"python3 -I {GATE} out/verify/x")))

    assert done.returncode == 0
    answer = json.loads(done.stdout)["hookSpecificOutput"]
    assert answer["hookEventName"] == "PreToolUse"
    assert answer["permissionDecision"] == "allow"
    assert "share_gate.py" in answer["permissionDecisionReason"]


def test_the_hook_stays_silent_otherwise() -> None:
    for body in (json.dumps(payload("git status")), "not json", "{}"):
        done = run_hook(body)
        assert done.returncode == 0 and done.stdout == ""


@pytest.mark.parametrize(
    "command",
    [
        f"python3 -I {GATE} 'a; rm -rf out'",
        f'python3 -I {GATE} "x | y" "(#12)"',
    ],
)
def test_operators_inside_quotes_are_plain_text(command: str) -> None:
    assert ALLOW.decide(payload(command)) is not None


@pytest.mark.parametrize(
    "command",
    [
        f'python3 -I {GATE} "$(whoami)"',
        f'python3 -I {GATE} "`whoami`"',
        f'python3 -I {GATE} "a\\"; rm x; echo "',
        f"python3 -I {GATE} x #'comment",
        f"python3 -I {GATE} *",
    ],
)
def test_substitution_and_unquoted_operators_are_never_plain(command: str) -> None:
    assert ALLOW.decide(payload(command)) is None
