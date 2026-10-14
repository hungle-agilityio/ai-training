from dataclasses import asdict

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from reviews import services


def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "reviews/dashboard.html", {"overview": services.dashboard_overview()})


def dashboard_api(request: HttpRequest) -> JsonResponse:
    scores = services.branch_scores()
    return JsonResponse({"branches": [asdict(score) for score in scores]})
