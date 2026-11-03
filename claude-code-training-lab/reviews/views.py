from dataclasses import asdict

from django.contrib.auth.decorators import login_not_required
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.utils import timezone

from reviews import services
from reviews.forms import PageForm, ReviewFilterForm

SITE_ICON = "reviews/icon.svg"


@login_not_required
def favicon(request: HttpRequest) -> HttpResponseRedirect:
    """Browsers that ask the old address before reading the page get the tab icon too."""
    return redirect(static(SITE_ICON))


@login_not_required
def healthz(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "reviews/dashboard.html", {"overview": services.dashboard_overview()})


def location(request: HttpRequest, pk: int) -> HttpResponse:
    page = services.location_page(pk)
    if page is None:
        raise Http404("No such location")
    return render(request, "reviews/location.html", {"page": page})


def reviews(request: HttpRequest) -> HttpResponse:
    page = services.reviews_page(
        PageForm(request.GET).page_number(),
        filters=ReviewFilterForm(request.GET).filters(),
    )
    return render(request, "reviews/reviews.html", {"page": page})


def dashboard_api(request: HttpRequest) -> JsonResponse:
    scores = services.branch_scores()
    return JsonResponse({"branches": [asdict(score) for score in scores]})


def reviews_export(request: HttpRequest) -> StreamingHttpResponse:
    filters = ReviewFilterForm(request.GET).filters()
    response = StreamingHttpResponse(
        services.reviews_csv(filters),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{services.export_filename_for(filters, timezone.now())}"'
    )
    return response
