from django.urls import URLPattern, URLResolver, path
from django.views.generic import RedirectView

from reviews import views

urlpatterns: list[URLPattern | URLResolver] = [
    path("", RedirectView.as_view(pattern_name="dashboard"), name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("reviews/", views.reviews, name="reviews"),
    path("api/dashboard/", views.dashboard_api, name="dashboard-api"),
]
