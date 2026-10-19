"""Главная страница и страница ошибки 404."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from lessons.presenters import build_lesson_items
from storage import load_schedule


def page_not_found(request: HttpRequest,
                   exception: Exception) -> HttpResponse:
    """Обработчик 404 (подключён как handler404 в roomly/urls.py)."""
    return render(request, "homepage/not_found.html", status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная: сводка по расписанию и занятия на сегодня."""
    schedule = load_schedule()
    lessons = build_lesson_items(schedule, schedule.lessons)
    context = {
        "today": timezone.localdate(),
        "has_data": bool(schedule),
        "lessons_count": len(schedule),
        "teachers_count": len(schedule.teachers),
        "rooms_count": len(schedule.rooms),
        "today_lessons": [item for item in lessons if item.is_today],
    }
    return render(request, "homepage/index.html", context)
