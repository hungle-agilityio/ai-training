from datetime import date

from django import forms

from reviews.search_text import tidy_search_input
from reviews.services import RATING_RANGES, ReviewFilters

WEEK_MIN_DAY = date(2000, 1, 1)
WEEK_MAX_DAY = date(2100, 12, 31)


class PageForm(forms.Form):
    page = forms.IntegerField(min_value=1, required=False)

    def page_number(self) -> int | None:
        if not self.is_valid():
            return None
        value: int | None = self.cleaned_data["page"]
        return value


class ReviewFilterForm(forms.Form):
    """Filters of the Reviews page. A wrong value is ignored; the other filters still apply."""

    search = forms.CharField(required=False)
    location = forms.IntegerField(min_value=1, required=False)
    rating = forms.ChoiceField(
        choices=[("", "All ratings"), *[(key, key) for key in RATING_RANGES]], required=False
    )
    week = forms.DateField(input_formats=["%Y-%m-%d"], required=False)

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
        )
