from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from reviews import goal_views, template_repository
from reviews.template_forms import TemplateForm


@require_http_methods(["GET", "POST"])
def templates_add(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return redirect(reverse("settings"))
    form = TemplateForm(request.POST.dict())
    if form.is_valid():
        template_repository.create_template(name=form.name, text=form.text, kind=form.kind)
        return redirect(reverse("settings") + "?templates=added#settings-templates")
    context = goal_views.settings_context(request, template_form=form)
    return render(request, "reviews/settings.html", context)
