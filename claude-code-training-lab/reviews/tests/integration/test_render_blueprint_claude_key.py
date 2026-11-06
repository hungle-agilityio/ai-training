import re
from pathlib import Path

BLUEPRINT = Path(__file__).resolve().parents[4] / "render.yaml"


def test_claude_key_is_declared_without_a_value() -> None:
    text = BLUEPRINT.read_text()
    assert re.search(r"- key: ANTHROPIC_API_KEY\n\s+sync: false", text)
    assert not re.search(r"key: ANTHROPIC_API_KEY\s+value:", text)
