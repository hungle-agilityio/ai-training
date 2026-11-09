from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from reviews import topic_service
from reviews.topic_forms import PERIOD_CHOICES, TopicFilterForm


def topics(request: HttpRequest) -> HttpResponse:
    form = TopicFilterForm(request.GET)
    locations = topic_service.location_options()
    location_id = form.location_id({pk for pk, _ in locations})
    period_days = form.period_days()
    overview = topic_service.topic_overview(location_id, period_days, timezone.now())
    filtered = location_id is not None or period_days is not None
    context = {
        "overview": overview,
        "locations": locations,
        "location_id": location_id,
        "periods": PERIOD_CHOICES,
        "period": str(period_days or ""),
        "is_empty": overview.review_count == 0 and not filtered,
        "summary": topic_service.summary_line(overview),
    }
    return render(request, "reviews/topics.html", context)
