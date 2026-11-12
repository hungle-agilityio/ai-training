import re
from pathlib import Path

BLUEPRINT = Path(__file__).resolve().parents[4] / "render.yaml"


def test_sentry_dsn_is_declared_as_a_secret_not_written() -> None:
    text = BLUEPRINT.read_text()
    assert re.search(r"- key: SENTRY_DSN\s+sync: false", text)
    assert not re.search(r"key: SENTRY_DSN\s+value:", text)
