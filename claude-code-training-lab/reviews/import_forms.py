from django import forms

from reviews.import_service import MAX_BYTES

MSG_NO_FILE = "Choose a CSV file to import."


class ImportForm(forms.Form):
    file = forms.FileField(
        label="CSV file",
        error_messages={"required": MSG_NO_FILE, "empty": MSG_NO_FILE, "invalid": MSG_NO_FILE},
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}),
    )

    def file_bytes(self) -> bytes:
        """The uploaded bytes, read up to one byte over the limit so the service can refuse it."""
        data: bytes = self.cleaned_data["file"].read(MAX_BYTES + 1)
        return data
