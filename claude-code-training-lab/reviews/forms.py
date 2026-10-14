from django import forms


class PageForm(forms.Form):
    page = forms.IntegerField(min_value=1, required=False)

    def page_number(self) -> int | None:
        if not self.is_valid():
            return None
        value: int | None = self.cleaned_data["page"]
        return value
