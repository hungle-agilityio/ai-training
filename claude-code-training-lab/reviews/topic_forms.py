from django import forms

PERIOD_CHOICES = (("", "All time"), ("30", "Last 30 days"), ("90", "Last 90 days"))


class TopicFilterForm(forms.Form):
    """Filters of the Topics page. A wrong value is ignored; the other filter still applies."""

    location = forms.IntegerField(min_value=1, required=False)
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False)

    def location_id(self, known: set[int]) -> int | None:
        self.is_valid()
        value: int | None = self.cleaned_data.get("location")
        return value if value in known else None

    def period_days(self) -> int | None:
        self.is_valid()
        value = self.cleaned_data.get("period")
        return int(value) if value else None
