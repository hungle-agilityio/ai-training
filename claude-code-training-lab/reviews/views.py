from dataclasses import asdict

from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone

from reviews import services
from reviews.forms import PageForm, ReviewFilterForm


def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "reviews/dashboard.html", {"overview": services.dashboard_overview()})


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
    response = StreamingHttpResponse(
        services.reviews_csv(ReviewFilterForm(request.GET).filters()),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{services.export_filename(timezone.now())}"'
    )
    return response
