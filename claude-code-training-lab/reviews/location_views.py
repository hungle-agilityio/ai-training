from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from reviews import goal_repository, goal_views, location_repository
from reviews.location_forms import LocationForm


@require_http_methods(["GET", "POST"])
def locations_add(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return redirect(reverse("settings"))
    locations = goal_repository.location_goals()
    form = LocationForm(request.POST.dict(), [location.name for location in locations])
    if form.is_valid():
        location_repository.add_location(form.name)
        return redirect(reverse("settings") + "?locations=added#settings-locations")
    context = goal_views.settings_context(request, location_form=form, locations=locations)
    return render(request, "reviews/settings.html", context)
