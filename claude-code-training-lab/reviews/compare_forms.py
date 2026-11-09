from django import forms

from reviews.topic_forms import PERIOD_CHOICES


class CompareForm(forms.Form):
    """Inputs of the Compare page. A wrong value counts as not chosen, never as an error."""

    a = forms.IntegerField(min_value=1, required=False)
    b = forms.IntegerField(min_value=1, required=False)
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False)

    def _id(self, field: str, known: set[int]) -> int | None:
        self.is_valid()
        value: int | None = self.cleaned_data.get(field)
        return value if value in known else None

    def a_id(self, known: set[int]) -> int | None:
        return self._id("a", known)

    def b_id(self, known: set[int]) -> int | None:
        return self._id("b", known)

    def raw_ids(self) -> tuple[int | None, int | None]:
        """The two chosen ids as typed; whether they are locations is the service's answer."""
        self.is_valid()
        return self.cleaned_data.get("a"), self.cleaned_data.get("b")

    def period_days(self) -> int | None:
        self.is_valid()
        value = self.cleaned_data.get("period")
        return int(value) if value else None
