from django.contrib.auth import views as auth_views
from django.urls import URLPattern, URLResolver, path
from django.views.generic import RedirectView

from reviews import (
    compare_views,
    goal_views,
    import_views,
    location_views,
    template_views,
    topic_views,
    views,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("healthz/", views.healthz, name="healthz"),
    path("favicon.ico", views.favicon),
    path("", RedirectView.as_view(pattern_name="dashboard"), name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("locations/<int:pk>/", views.location, name="location"),
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/import/", import_views.reviews_import, name="reviews-import"),
    path("reviews/export/", views.reviews_export, name="reviews-export"),
    path("reviews/<int:pk>/reply/", views.review_reply, name="review-reply"),
    path("replies/", views.replies, name="replies"),
    path("settings/", views.settings_page, name="settings"),
    path("settings/goals/", goal_views.goals_save, name="settings-goals"),
    path("settings/locations/", location_views.locations_add, name="settings-locations"),
    path("settings/templates/", template_views.templates_add, name="settings-templates"),
    path(
        "settings/templates/<int:template_id>/",
        template_views.template_edit,
        name="settings-template-edit",
    ),
    path(
        "settings/templates/<int:template_id>/delete/",
        template_views.template_delete,
        name="settings-template-delete",
    ),
    path("reports/", views.reports, name="reports"),
    path("reports/export/", views.reports_export, name="reports-export"),
    path("topics/", topic_views.topics, name="topics"),
    path("compare/", compare_views.compare, name="compare"),
    path("compare/export/", compare_views.compare_export, name="compare-export"),
    path("api/dashboard/", views.dashboard_api, name="dashboard-api"),
]
