import subprocess
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]


def _is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=LAB_DIR, check=False, capture_output=True
    )
    return result.returncode == 0


def test_agent_env_is_ignored() -> None:
    assert _is_ignored("ops/agent.env")


def test_agent_env_example_is_not_ignored() -> None:
    assert not _is_ignored("ops/agent.env.example")
