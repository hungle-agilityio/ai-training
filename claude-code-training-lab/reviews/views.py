from dataclasses import asdict

from django.http import HttpRequest, JsonResponse

from reviews import services


def dashboard(request: HttpRequest) -> JsonResponse:
    scores = services.branch_scores()
    return JsonResponse({"branches": [asdict(score) for score in scores]})
