"""Корневая маршрутизация проекта roomly."""

from django.contrib import admin
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Учебный проект: статика (CSS, JS, логотип) отдаётся самим Django
    # даже при DEBUG = False, чтобы работал обычный runserver и при этом
    # была видна своя страница 404. В реальном проекте статику отдаёт
    # веб-сервер (nginx) после collectstatic.
    path("static/<path:path>", serve_static, {"insecure": True}),
    path("lessons/", include("lessons.urls")),
    path("teachers/", include("teachers.urls")),
    path("rooms/", include("rooms.urls")),
    # Самый общий маршрут (пустой префикс) — в самом конце.
    path("", include("homepage.urls")),
]

# Django читает handler404 только из корневого urls.py (ROOT_URLCONF).
handler404 = "homepage.views.page_not_found"
