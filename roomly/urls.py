"""Корневая маршрутизация проекта roomly."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("lessons/", include("lessons.urls")),
    path("teachers/", include("teachers.urls")),
    path("rooms/", include("rooms.urls")),
    # Самый общий маршрут (пустой префикс) — в самом конце.
    path("", include("homepage.urls")),
]

# Django читает handler404 только из корневого urls.py (ROOT_URLCONF).
handler404 = "homepage.views.page_not_found"
