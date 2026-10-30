from django.contrib.auth import views as auth_views
from django.urls import URLPattern, URLResolver, path
from django.views.generic import RedirectView

from reviews import views

urlpatterns: list[URLPattern | URLResolver] = [
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("healthz/", views.healthz, name="healthz"),
    path("", RedirectView.as_view(pattern_name="dashboard"), name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/export/", views.reviews_export, name="reviews-export"),
    path("api/dashboard/", views.dashboard_api, name="dashboard-api"),
]
