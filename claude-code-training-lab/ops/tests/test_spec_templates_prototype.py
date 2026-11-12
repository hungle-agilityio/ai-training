"""The spec templates name prototype states instead of a design card.

Spec: specs/app-prototype/spec.md (AC14, AC15; rows M13 and M14 of its test matrix).
Run: pytest ops/tests/test_spec_templates_prototype.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
TEMPLATES = APP / "docs" / "app" / "templates" / "spec"
SPEC = TEMPLATES / "spec.md"
TASKS = TEMPLATES / "tasks.md"

DESIGN_PLACEHOLDER = (
    "<the prototype states this feature adds or changes, as #<state> ids of "
    'design/app/prototype.html, approved with "Prototype ổn"; or "nothing visible to users">'
)
BUILD_SENTENCE = (
    'Every step whose page has a state in design/app/prototype.html names it with "design"; '
    "the verify report shows that state next to the built screen."
)


def _design_section(text: str) -> str:
    match = re.search(r"^## Design\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match is not None, "spec template has no ## Design section"
    return match.group(1)


def _screens_example(text: str) -> dict[str, list[dict[str, str]]]:
    match = re.search(r"## Screens to capture\s*```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    assert match is not None, "tasks template has no json example under Screens to capture"
    parsed: dict[str, list[dict[str, str]]] = json.loads(match.group(1))
    return parsed


def test_spec_design_placeholder_names_prototype_states() -> None:
    lines = [line.strip() for line in _design_section(SPEC.read_text()).splitlines()]
    assert DESIGN_PLACEHOLDER in lines


def test_spec_template_has_no_design_card_words() -> None:
    assert "design card" not in SPEC.read_text()


def test_tasks_example_parses_as_json_with_design_key() -> None:
    steps = _screens_example(TASKS.read_text())["steps"]
    assert len(steps) == 1
    assert steps[0] == {
        "name": "reviews-filters",
        "goto": "/reviews/",
        "capture": "#filter-rating",
        "design": "reviews-filtered",
    }


def test_tasks_comment_explains_design_key_after_copy_sentence() -> None:
    text = TASKS.read_text()
    first = "The build copies the block unchanged into `build_report.py --browser --spec`."
    line = next(ln for ln in text.splitlines() if ln.lstrip().startswith(first))
    assert line.lstrip().startswith(f"{first} {BUILD_SENTENCE}")
