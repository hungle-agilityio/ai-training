from collections.abc import Mapping
from dataclasses import dataclass

from django import forms

from reviews.followup import NOTE_ERROR, STATUS_ERROR, STATUS_LABELS, followup_errors
from reviews.reply_service import FollowUpInfo

SAVED = "saved"


class FollowUpSavedForm(forms.Form):
    """The `followup` flag of the reply page; only the value `saved` counts."""

    followup = forms.ChoiceField(choices=[(SAVED, SAVED)], required=False)

    def is_saved(self) -> bool:
        return self.is_valid() and self.cleaned_data["followup"] == SAVED


class FollowUpForm:
    """Reads the status and note of a follow-up change; one error at most per field."""

    def __init__(self, data: Mapping[str, str]) -> None:
        self.status = data.get("status", "")
        # Browsers send a line break as two characters; it counts as one, as in the textarea.
        self.note = data.get("note", "").replace("\r\n", "\n")
        messages = followup_errors(self.status, self.note)
        self.status_error = STATUS_ERROR if STATUS_ERROR in messages else ""
        self.note_error = NOTE_ERROR if NOTE_ERROR in messages else ""

    def is_valid(self) -> bool:
        return not (self.status_error or self.note_error)


@dataclass(frozen=True)
class StatusOption:
    value: str
    label: str
    selected: bool


@dataclass(frozen=True)
class FollowUpBox:
    options: list[StatusOption]
    note: str
    status_error: str
    note_error: str
    saved: bool


def followup_box(
    info: FollowUpInfo | None, *, form: FollowUpForm | None = None, saved: bool = False
) -> FollowUpBox | None:
    """The box shows what was typed when a change is refused, else the stored case."""
    if info is None:
        return None
    status = form.status if form is not None else info.status
    return FollowUpBox(
        options=[
            StatusOption(value, label, value == status) for value, label in STATUS_LABELS.items()
        ],
        note=form.note if form is not None else info.note,
        status_error=form.status_error if form is not None else "",
        note_error=form.note_error if form is not None else "",
        saved=saved,
    )
