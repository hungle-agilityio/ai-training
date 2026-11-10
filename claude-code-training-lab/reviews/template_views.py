from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from reviews import goal_views, template_repository
from reviews.models import ReplyTemplate
from reviews.reply_templates import KIND_LABELS
from reviews.template_forms import KIND_ORDER, TemplateForm


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


def _get_or_404(template_id: int) -> ReplyTemplate:
    template = template_repository.get_template(template_id)
    if template is None:
        raise Http404("No such reply template")
    return template


@require_http_methods(["GET", "POST"])
def template_edit(request: HttpRequest, template_id: int) -> HttpResponse:
    template = _get_or_404(template_id)
    form: TemplateForm | None = None
    if request.method == "POST":
        form = TemplateForm(request.POST.dict(), exclude_id=template.id)
        if form.is_valid():
            template_repository.update_template(
                template.id, name=form.name, text=form.text, kind=form.kind
            )
            return redirect(reverse("settings") + "?templates=saved#settings-templates")
    typed = {"name": template.name, "kind": template.kind, "text": template.text}
    context = {
        "template": template,
        "template_kinds": [(kind, KIND_LABELS[kind]) for kind in KIND_ORDER],
        "template_typed": form.typed if form else typed,
        "template_errors": form.errors if form else {},
    }
    return render(request, "reviews/template_edit.html", context)


@require_http_methods(["GET", "POST"])
def template_delete(request: HttpRequest, template_id: int) -> HttpResponse:
    template = _get_or_404(template_id)
    if request.method == "POST":
        template_repository.delete_template(template.id)
        return redirect(reverse("settings") + "?templates=deleted#settings-templates")
    return render(request, "reviews/template_delete.html", {"template": template})
