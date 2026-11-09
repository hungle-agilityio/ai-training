from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from reviews import import_service
from reviews.import_forms import ImportForm
from reviews.import_service import ImportResult

MAX_ERRORS_SHOWN = 50


@require_http_methods(["GET", "POST"])
def reviews_import(request: HttpRequest) -> HttpResponse:
    if request.resolver_match is not None:
        request.resolver_match.url_name = "reviews"  # the sidebar marks Reviews as current
    form = ImportForm(request.POST, request.FILES) if request.method == "POST" else ImportForm()
    result: ImportResult | None = None
    refusal: str | None = None
    if request.method == "POST":
        if form.is_valid():
            result = import_service.import_reviews(form.file_bytes(), now=timezone.now())
            refusal = result.refusal
            if refusal is not None:
                result = None
        else:
            refusal = str(form.errors["file"][0])
    context = {
        "form": ImportForm(),
        "result": result,
        "refusal": refusal,
        "shown_errors": result.errors[:MAX_ERRORS_SHOWN] if result else (),
        "more_errors": max(len(result.errors) - MAX_ERRORS_SHOWN, 0) if result else 0,
    }
    return render(request, "reviews/import.html", context)
