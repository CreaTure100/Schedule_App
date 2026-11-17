"""Корневая маршрутизация проекта roomly."""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import include, path

from homepage.views import serve_media

urlpatterns = [
    path("admin/", admin.site.urls),
    # Учебный проект: статика (CSS, JS, логотип) отдаётся самим Django
    # даже при DEBUG = False, чтобы работал обычный runserver и при этом
    # была видна своя страница 404. В реальном проекте статику отдаёт
    # веб-сервер (nginx) после collectstatic.
    path("static/<path:path>", serve_static, {"insecure": True}),
    # ПР11: загруженные изображения. Помощник static() работает только
    # при DEBUG = True, а в проекте по умолчанию DEBUG = False, поэтому,
    # как и статику, медиафайлы отдаёт сам Django (только для учёбы).
    path(f"{settings.MEDIA_URL.lstrip('/')}<path:path>", serve_media),
    path("lessons/", include("lessons.urls")),
    path("teachers/", include("teachers.urls")),
    path("rooms/", include("rooms.urls")),
    path("db/", include("dbpages.urls")),
    # Самый общий маршрут (пустой префикс) — в самом конце.
    path("", include("homepage.urls")),
]

# ПР10: маршруты Django Debug Toolbar (только при ROOMLY_DEBUG=1 и
# установленном пакете, см. settings.USE_DEBUG_TOOLBAR).
if settings.USE_DEBUG_TOOLBAR:
    urlpatterns = [
        path("__debug__/", include("debug_toolbar.urls")),
    ] + urlpatterns

# Django читает handler404 только из корневого urls.py (ROOT_URLCONF).
handler404 = "homepage.views.page_not_found"
