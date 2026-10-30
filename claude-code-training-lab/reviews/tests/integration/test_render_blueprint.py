import re
from pathlib import Path

import pytest

BLUEPRINT = Path(__file__).resolve().parents[4] / "render.yaml"


@pytest.fixture
def blueprint() -> str:
    return BLUEPRINT.read_text()


def _value(text: str, key: str) -> str:
    match = re.search(rf"^\s*-?\s*{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    assert match, f"{key} missing"
    return match.group(1).strip("\"'")


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("type", "web"),
        ("name", "reviewradar"),
        ("runtime", "python"),
        ("plan", "free"),
        ("region", "singapore"),
        ("rootDir", "claude-code-training-lab"),
        ("branch", "main"),
        ("autoDeployTrigger", "checksPass"),
        ("healthCheckPath", "/dashboard/"),
    ],
)
def test_service_setting(blueprint: str, key: str, expected: str) -> None:
    assert _value(blueprint, key) == expected


def test_build_installs_locked_runtime_dependencies_only(blueprint: str) -> None:
    build = _value(blueprint, "buildCommand")
    assert "uv sync --frozen --no-dev" in build
    assert "collectstatic --noinput" in build


def test_start_runs_migrate_then_seed_then_gunicorn(blueprint: str) -> None:
    start = _value(blueprint, "startCommand")
    positions = [start.index(step) for step in ("migrate --noinput", "seed_demo_data", "gunicorn")]
    assert positions == sorted(positions)
    assert "reviewradar.wsgi" in start
    assert "$PORT" in start
    assert "&&" in start


def test_debug_is_off_and_host_is_set(blueprint: str) -> None:
    assert re.search(r'key: DJANGO_DEBUG\s+value: "0"', blueprint)
    assert re.search(r"key: DJANGO_ALLOWED_HOSTS\s+value: reviewradar\.onrender\.com", blueprint)


def test_secret_key_is_generated_not_written(blueprint: str) -> None:
    assert re.search(r"key: DJANGO_SECRET_KEY\s+generateValue: true", blueprint)
    assert not re.search(r"key: DJANGO_SECRET_KEY\s+value:", blueprint)


def test_python_version_is_3_11(blueprint: str) -> None:
    assert re.search(r'key: PYTHON_VERSION\s+value: "3\.11', blueprint)
