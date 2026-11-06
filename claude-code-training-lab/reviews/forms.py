from datetime import date
from typing import Any

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

from reviews import reply_service
from reviews.search_text import tidy_search_input
from reviews.services import RATING_RANGES, REPLY_CHOICES, ReviewFilters

WEEK_MIN_DAY = date(2000, 1, 1)
WEEK_MAX_DAY = date(2100, 12, 31)


class PageForm(forms.Form):
    page = forms.IntegerField(min_value=1, required=False)

    def page_number(self) -> int | None:
        if not self.is_valid():
            return None
        value: int | None = self.cleaned_data["page"]
        return value


class ReplyForm(forms.Form):
    """The reply box of one review; the text is kept as typed so it can be shown again."""

    text = forms.CharField(required=False, strip=False)

    def typed(self) -> str:
        self.is_valid()
        return str(self.cleaned_data.get("text", "")).replace("\r\n", "\n")

    def reply_text(self) -> str | None:
        return reply_service.clean_reply_text(self.typed())


class SavedForm(forms.Form):
    """The `saved` flag of the Reply drafts page; only the value 1 counts."""

    saved = forms.ChoiceField(choices=[("1", "1")], required=False)

    def is_saved(self) -> bool:
        return self.is_valid() and self.cleaned_data["saved"] == "1"


class AccountPasswordForm(PasswordChangeForm):
    """Django's PasswordChangeForm with the labels of the Settings page."""

    def __init__(self, user: User, *args: Any, **kwargs: Any) -> None:
        super().__init__(user, *args, **kwargs)
        self.fields["old_password"].widget.attrs.pop("autofocus", None)
        self.fields["old_password"].label = "Current password"
        self.fields["new_password2"].label = "Confirm new password"
        self.fields["new_password2"].help_text = ""


class ReportMonthForm(forms.Form):
    """Month picker of the Monthly report. A wrong value is ignored: the report shows this month."""

    def month(self) -> date | None:
        raw = str(self.data.get("month", ""))
        year, _, number = raw.partition("-")
        if len(year) != 4 or len(number) != 2 or not (year + number).isdigit():
            return None
        try:
            return date(int(year), int(number), 1)
        except ValueError:
            return None


class ReviewFilterForm(forms.Form):
    """Filters of the Reviews page. A wrong value is ignored; the other filters still apply."""

    search = forms.CharField(required=False)
    location = forms.IntegerField(min_value=1, required=False)
    rating = forms.ChoiceField(
        choices=[("", "All ratings"), *[(key, key) for key in RATING_RANGES]], required=False
    )
    week = forms.DateField(input_formats=["%Y-%m-%d"], required=False)
    reply = forms.ChoiceField(
        choices=[("", "All"), *[(key, key) for key in REPLY_CHOICES]], required=False
    )

    def clean_search(self) -> str:
        return tidy_search_input(self.cleaned_data["search"])

    def clean_week(self) -> date | None:
        day: date | None = self.cleaned_data["week"]
        if day is not None and not WEEK_MIN_DAY <= day <= WEEK_MAX_DAY:
            raise forms.ValidationError("Choose a day between 2000 and 2100.")
        return day

    def filters(self) -> ReviewFilters:
        self.is_valid()
        data = self.cleaned_data
        return ReviewFilters(
            branch_id=data.get("location") or None,
            rating=data.get("rating") or None,
            day=data.get("week") or None,
            search=data.get("search") or "",
            reply=data.get("reply") or None,
        )
