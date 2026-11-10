from dataclasses import asdict
from typing import cast

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.models import User
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from reviews import (
    goal_views,
    reply_service,
    reply_suggestion,
    report_service,
    services,
    topic_service,
    trend_service,
)
from reviews.forms import (
    AccountPasswordForm,
    OverdueForm,
    PageForm,
    ReplyForm,
    ReportMonthForm,
    ReviewFilterForm,
    SavedForm,
)

SITE_ICON = "reviews/icon.svg"


@login_not_required
def favicon(request: HttpRequest) -> HttpResponseRedirect:
    """Browsers that ask the old address before reading the page get the tab icon too."""
    return redirect(static(SITE_ICON))


@login_not_required
def healthz(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "reviews/dashboard.html", {"overview": services.dashboard_overview()})


def location(request: HttpRequest, pk: int) -> HttpResponse:
    page = services.location_page(pk)
    if page is None:
        raise Http404("No such location")
    trend = trend_service.weekly_trend(pk, timezone.now())
    topics = topic_service.location_topics(pk)
    context = {"page": page, "trend": trend, "topics": topics}
    return render(request, "reviews/location.html", context)


def reviews(request: HttpRequest) -> HttpResponse:
    page = services.reviews_page(
        PageForm(request.GET).page_number(),
        filters=ReviewFilterForm(request.GET).filters(),
    )
    return render(request, "reviews/reviews.html", {"page": page})


def replies(request: HttpRequest) -> HttpResponse:
    page = reply_service.replies_page(
        PageForm(request.GET).page_number(),
        overdue_only=OverdueForm(request.GET).is_overdue(),
    )
    saved = SavedForm(request.GET).is_saved()
    return render(request, "reviews/replies.html", {"page": page, "saved": saved})


@require_http_methods(["GET", "POST"])
def settings_page(request: HttpRequest) -> HttpResponse:
    form = AccountPasswordForm(
        cast(User, request.user), request.POST if request.method == "POST" else None
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        return redirect(reverse("settings") + "?saved=1")
    context = goal_views.settings_context(request, password_form=form)
    return render(request, "reviews/settings.html", context)


@require_http_methods(["GET", "POST"])
def review_reply(request: HttpRequest, pk: int) -> HttpResponse:
    typed: str | None = None
    invalid = False
    suggestion: reply_suggestion.ReplySuggestion | None = None
    if request.method == "POST":
        form = ReplyForm(request.POST)
        typed = form.typed()
        if form.wants_suggestion():
            suggestion = reply_suggestion.suggest_reply(pk)
            if suggestion is None:
                raise Http404("No such review")
            if suggestion.status == "ok":
                typed = suggestion.draft
        else:
            text = form.reply_text()
            if text is not None:
                user_id = request.user.pk if request.user.is_authenticated else None
                if not reply_service.save_reply(pk, text, user_id, timezone.now()):
                    raise Http404("No such review")
                return redirect(f"{reverse('replies')}?saved=1")
            invalid = True
    target = reply_service.reply_target(pk)
    if target is None:
        raise Http404("No such review")
    return render(
        request,
        "reviews/reply.html",
        {
            "target": target,
            "typed": typed,
            "invalid": invalid,
            "suggest_on": reply_suggestion.suggestion_mode() != "off",
            "suggest_status": suggestion.status if suggestion is not None else "",
        },
    )


def reports(request: HttpRequest) -> HttpResponse:
    report = report_service.monthly_report(ReportMonthForm(request.GET).month(), timezone.now())
    return render(request, "reviews/reports.html", {"report": report})


def reports_export(request: HttpRequest) -> HttpResponse:
    report = report_service.monthly_report(ReportMonthForm(request.GET).month(), timezone.now())
    response = HttpResponse(
        report_service.report_csv(report), content_type="text/csv; charset=utf-8"
    )
    filename = report_service.report_filename(report)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def dashboard_api(request: HttpRequest) -> JsonResponse:
    scores = services.branch_scores()
    return JsonResponse({"branches": [asdict(score) for score in scores]})


def reviews_export(request: HttpRequest) -> StreamingHttpResponse:
    filters = ReviewFilterForm(request.GET).filters()
    response = StreamingHttpResponse(
        services.reviews_csv(filters),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{services.export_filename_for(filters, timezone.now())}"'
    )
    return response
