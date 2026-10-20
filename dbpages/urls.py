"""Маршруты приложения dbpages (подключены с префиксом db/)."""

from django.urls import path

from . import views

app_name = "dbpages"

urlpatterns = [
    path("lessons/", views.lesson_list, name="lessons"),
    path("teachers/", views.teacher_list, name="teachers"),
    path("today/", views.today_lessons, name="today"),
    path("search/", views.search_lessons, name="search"),
    path("stats/", views.stats, name="stats"),
]
