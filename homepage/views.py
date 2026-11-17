"""Главная страница и страница ошибки 404."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from lessons import presenters as lesson_presenters
from lessons.models import Lesson
from rooms.models import Room
from teachers.models import Teacher


def page_not_found(request: HttpRequest,
                   exception: Exception) -> HttpResponse:
    """Обработчик 404 (подключён как handler404 в roomly/urls.py)."""
    return render(request, "homepage/not_found.html", status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная: сводка по расписанию и занятия на сегодня."""
    today_lessons = (
        Lesson.objects
        .on_day(lesson_presenters.today_number())
        .with_related()
        .order_by("start_time", "pk")
    )
    context = {
        "today": timezone.localdate(),
        "has_data": Lesson.objects.exists(),
        "lessons_count": Lesson.objects.count(),
        "teachers_count": Teacher.objects.count(),
        "rooms_count": Room.objects.count(),
        "today_lessons": lesson_presenters.build_lesson_items(today_lessons),
    }
    return render(request, "homepage/index.html", context)
