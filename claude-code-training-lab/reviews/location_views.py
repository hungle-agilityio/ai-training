from django.http import Http404, HttpRequest, HttpResponse
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


@require_http_methods(["GET", "POST"])
def location_rename(request: HttpRequest, location_id: int) -> HttpResponse:
    location = location_repository.get_location(location_id)
    if location is None:
        raise Http404("No such location")
    form: LocationForm | None = None
    if request.method == "POST":
        taken = location_repository.other_location_names(location.location_id)
        form = LocationForm(request.POST.dict(), taken)
        if form.is_valid():
            location_repository.rename_location(location.location_id, form.name)
            return redirect(reverse("settings") + "?locations=renamed#settings-locations")
    context = {
        "location": location,
        "location_typed": form.typed if form else location.name,
        "location_errors": form.errors if form else [],
    }
    return render(request, "reviews/location_rename.html", context)
