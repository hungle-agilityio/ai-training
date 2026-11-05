from pathlib import Path

START_LOOP = Path(__file__).resolve().parents[1] / "start-loop.sh"


def test_start_loop_sleeps_five_minutes_between_ticks() -> None:
    text = START_LOOP.read_text()
    assert "sleep 300" in text
    assert "sleep 600" not in text
    assert "every 5 minutes" in text
