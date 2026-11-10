from collections.abc import Mapping

from reviews import template_repository
from reviews.reply_templates import KIND_LABELS, NAME_ERROR, template_errors

KIND_ORDER = ("any", "good", "bad")
KIND_ERROR = "Choose a kind."
DUPLICATE_ERROR = "A template with this name already exists."


class TemplateForm:
    """Reads name, kind and text of a new or edited template; errors are kept per field."""

    def __init__(self, data: Mapping[str, str], exclude_id: int | None = None) -> None:
        self.name = data.get("name", "").strip()
        self.kind = data.get("kind", "")
        self.text = data.get("text", "").strip()
        self.typed: dict[str, str] = {
            "name": data.get("name", ""),
            "kind": self.kind,
            "text": data.get("text", ""),
        }
        self.errors: dict[str, list[str]] = {}
        for message in template_errors(self.name, self.text):
            self.errors.setdefault("name" if message == NAME_ERROR else "text", []).append(message)
        if self.kind not in KIND_LABELS:
            self.errors["kind"] = [KIND_ERROR]
        if "name" not in self.errors and template_repository.name_exists(self.name, exclude_id):
            self.errors["name"] = [DUPLICATE_ERROR]

    def is_valid(self) -> bool:
        return not self.errors
