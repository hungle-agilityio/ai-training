from dataclasses import dataclass
from typing import Any, cast

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from reviews import goal_repository, settings_service
from reviews.forms import AccountPasswordForm, SavedForm
from reviews.goal_forms import GoalsForm
from reviews.goal_repository import LocationGoal


@dataclass(frozen=True)
class GoalField:
    location_id: int
    name: str
    value: str
    error: str | None


def goal_fields(locations: list[LocationGoal], form: GoalsForm | None = None) -> list[GoalField]:
    """One field per location; after a refused post it keeps what was typed and the error."""
    fields = []
    for location in locations:
        typed = form.typed.get(location.location_id) if form is not None else None
        if typed is None:
            typed = "" if location.goal is None else str(location.goal)
        error = form.errors.get(location.location_id) if form is not None else None
        fields.append(GoalField(location.location_id, location.name, typed, error))
    return fields


def settings_context(
    request: HttpRequest,
    password_form: AccountPasswordForm | None = None,
    goal_form: GoalsForm | None = None,
) -> dict[str, Any]:
    """Everything the settings page shows, so a refused form renders the whole page."""
    return {
        "form": password_form or AccountPasswordForm(cast(User, request.user), None),
        "saved": SavedForm(request.GET).is_saved(),
        "goals_saved": request.GET.get("goals") == "saved",
        "goal_fields": goal_fields(goal_repository.location_goals(), goal_form),
        "suggestions": settings_service.suggestion_status(),
    }


@require_http_methods(["GET", "POST"])
def goals_save(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return redirect(reverse("settings"))
    form = GoalsForm(request.POST.dict(), goal_repository.location_goals())
    if form.is_valid():
        goal_repository.save_goals(form.goals)
        return redirect(reverse("settings") + "?goals=saved")
    return render(request, "reviews/settings.html", settings_context(request, goal_form=form))
