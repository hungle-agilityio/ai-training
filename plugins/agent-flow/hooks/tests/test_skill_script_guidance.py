"""A loop build that writes a skill script in a refused form is told the plain form (#334).

Run: uv run pytest ../plugins/agent-flow/hooks/tests --no-cov -q (from the app folder)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
PLUGIN = HOOKS.parent
HOOK = HOOKS / "before-skill-script-allow.py"
REPORT = PLUGIN / "skills" / "build-verify-report" / "build_report.py"
NOT_LOOP: dict[str, str] = {}
LOOPS = ({"FLOW_LOOP": "1"}, {"REVIEWRADAR_LOOP": "1"})
ANY_MODE = (NOT_LOOP, *LOOPS)
VARIABLE_FORM = f"S=/private/tmp/x; uv run python {REPORT} --criteria $S/criteria.json"
PIPE_FORM = f"uv run python {REPORT} --no-ui 2>&1 | tail -30"
PLAIN_FORM = f"uv run python {REPORT} --no-ui --criteria out/verify-input/criteria.json"
REFUSED_FORMS = (
    VARIABLE_FORM,
    PIPE_FORM,
    f"cd /tmp && uv run python {REPORT} --no-ui",
    f"uv run python {REPORT} --no-ui > out/report.txt",
)


def answer(command: str, env: dict[str, str], cwd: Path = PLUGIN) -> dict[str, str] | None:
    clean = {k: v for k, v in os.environ.items() if k not in ("FLOW_LOOP", "REVIEWRADAR_LOOP")}
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    done = subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**clean, **env},
        check=True,
    )
    return json.loads(done.stdout)["hookSpecificOutput"] if done.stdout.strip() else None


@pytest.mark.parametrize("env", LOOPS)
@pytest.mark.parametrize("command", REFUSED_FORMS)
def test_a_refused_form_is_denied_with_the_plain_form_in_loop_mode(
    command: str, env: dict[str, str]
) -> None:
    result = answer(command, env)

    assert result is not None
    assert result["permissionDecision"] == "deny"
    assert result["permissionDecisionReason"].startswith(
        "Run the agent-flow skill script as one plain command"
    )


@pytest.mark.parametrize(
    "words",
    ["no shell variable", "`;`", "`&&`", "pipe", "redirection", "`2>&1`", "absolute script path"],
)
def test_the_denial_names_every_form_to_avoid(words: str) -> None:
    result = answer(PIPE_FORM, LOOPS[0])

    assert result is not None
    assert words in result["permissionDecisionReason"]


def test_the_denial_shows_input_files_as_relative_paths() -> None:
    result = answer(VARIABLE_FORM, LOOPS[0])

    assert result is not None
    assert "out/verify-input/criteria.json" in result["permissionDecisionReason"]


def test_a_relative_script_path_in_a_refused_form_is_resolved_from_the_cwd() -> None:
    command = "uv run python skills/build-verify-report/build_report.py --no-ui 2>&1 | tail -5"

    assert answer(command, LOOPS[0], PLUGIN) is not None
    assert answer(command, LOOPS[0], PLUGIN / "hooks") is None


@pytest.mark.parametrize("command", REFUSED_FORMS)
def test_outside_loop_mode_a_refused_form_gets_no_answer(command: str) -> None:
    assert answer(command, NOT_LOOP) is None


@pytest.mark.parametrize("env", ANY_MODE)
def test_a_plain_call_is_allowed_in_both_modes(env: dict[str, str]) -> None:
    result = answer(PLAIN_FORM, env)

    assert result is not None
    assert result["permissionDecision"] == "allow"


@pytest.mark.parametrize("env", ANY_MODE)
@pytest.mark.parametrize(
    "command",
    [
        "git status; git log -1",
        "uv run pytest -q 2>&1 | tail -3",
        "S=x; uv run python ops/agent_tick.py 2>&1 | tail -3",
        f"S=x; uv run python {PLUGIN}/hooks/before-skill-script-allow.py | tail -3",
        f"uv run python {PLUGIN}/skills/build-verify-report/missing_script.py | tail -3",
        f"uv run python ops/agent_tick.py {REPORT}",
    ],
)
def test_a_command_that_names_no_skill_script_gets_no_answer(
    command: str, env: dict[str, str]
) -> None:
    assert answer(command, env) is None
