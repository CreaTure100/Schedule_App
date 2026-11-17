"""Маршруты приложения lessons (подключены с префиксом lessons/)."""

from django.urls import path

from . import views

app_name = "lessons"

urlpatterns = [
    path("", views.lesson_list, name="list"),
    # Статический маршрут create/ стоит раньше динамических.
    path("create/", views.lesson_create, name="create"),
    path("<int:lesson_id>/", views.lesson_detail, name="detail"),
    path("<int:lesson_id>/edit/", views.lesson_update, name="update"),
    path("<int:lesson_id>/cancel/", views.lesson_cancel, name="cancel"),
]
