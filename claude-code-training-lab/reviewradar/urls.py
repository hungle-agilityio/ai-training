from django.urls import URLPattern, URLResolver, path

from reviews import views

urlpatterns: list[URLPattern | URLResolver] = [
    path("dashboard/", views.dashboard, name="dashboard"),
]
