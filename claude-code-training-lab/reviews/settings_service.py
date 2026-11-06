from dataclasses import dataclass
from typing import Literal

from django.conf import settings

from reviews import reply_suggestion

DETAILS = {
    "live": "Staff can ask Claude for a reply draft on each review's reply page.",
    "fake": "No API key: the button gives a fixed sample draft and nothing is sent to Claude.",
    "off": 'The "Suggest a reply" button is hidden. Your ReviewRadar admin can turn it on.',
}
LABELS = {"live": "On", "fake": "Demo", "off": "Off"}
BADGES = {"live": "badge-positive", "fake": "badge-watch", "off": "badge-neutral"}


@dataclass(frozen=True)
class SuggestionStatus:
    mode: Literal["live", "fake", "off"]
    label: str
    detail: str
    model: str | None

    @property
    def badge(self) -> str:
        return BADGES[self.mode]


def suggestion_status() -> SuggestionStatus:
    """What the reply-suggestion button does now; never the key."""
    mode = reply_suggestion.suggestion_mode()
    model = settings.ANTHROPIC_MODEL if mode == "live" else None
    return SuggestionStatus(mode=mode, label=LABELS[mode], detail=DETAILS[mode], model=model)
