from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from reviews import compare_service, topic_service
from reviews.compare_forms import CompareForm
from reviews.topic_forms import PERIOD_CHOICES


def verdict(comparison: compare_service.Comparison) -> str:
    diff = comparison.difference
    if diff is None:
        return ""
    if diff == 0:
        return "Same score"
    way = "higher" if diff > 0 else "lower"
    return f"{comparison.a.name} scores {abs(diff):.1f} {way} than {comparison.b.name}"


def star_pairs(
    comparison: compare_service.Comparison | None,
) -> list[tuple[compare_service.StarRow, compare_service.StarRow]]:
    if comparison is None:
        return []
    return list(zip(comparison.a.star_rows, comparison.b.star_rows, strict=True))


def compare(request: HttpRequest) -> HttpResponse:
    form = CompareForm(request.GET)
    locations = topic_service.location_options()
    known = {pk for pk, _ in locations}
    a_id, b_id = form.a_id(known), form.b_id(known)
    period_days = form.period_days()
    comparison = None
    if a_id is not None and b_id is not None and a_id != b_id:
        comparison = compare_service.compare_locations(a_id, b_id, period_days, timezone.now())
    context = {
        "locations": locations,
        "periods": PERIOD_CHOICES,
        "period": str(period_days or ""),
        "a_id": a_id,
        "b_id": b_id,
        "comparison": comparison,
        "verdict": verdict(comparison) if comparison else "",
        "star_pairs": star_pairs(comparison),
        "same_location": a_id is not None and a_id == b_id,
    }
    return render(request, "reviews/compare.html", context)
