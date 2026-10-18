"""Маршруты приложения lessons (подключены с префиксом lessons/)."""

from django.urls import path

from . import views

app_name = "lessons"

urlpatterns = [
    path("", views.lesson_list, name="list"),
    path("<int:lesson_id>/", views.lesson_detail, name="detail"),
]
