"""The four commands loop builds were refused are in the allow list (#335)."""

import json
from pathlib import Path

import pytest

SETTINGS = Path(__file__).resolve().parents[2] / ".claude" / "settings.json"
NEEDED_RULES = (
    "Read(~/.claude/plugins/cache/ai-training/agent-flow/**)",
    "Bash(uv sync:*)",
    "Bash(git mv:*)",
    "Bash(git cherry-pick:*)",
)


@pytest.mark.parametrize("rule", NEEDED_RULES)
def test_the_rule_a_loop_build_needs_is_allowed(rule: str) -> None:
    allowed = json.loads(SETTINGS.read_text())["permissions"]["allow"]

    assert rule in allowed
