"""Страницы приложения «Занятия»."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from lessons.presenters import (
    build_day_groups, build_lesson_item, build_lesson_items,
)
from schedule import get_day_status
from storage import load_schedule


def lesson_list(request: HttpRequest) -> HttpResponse:
    """Список занятий, сгруппированных по дням недели."""
    schedule = load_schedule()
    context = {
        "lessons": build_lesson_items(schedule, schedule.lessons),
        "days": build_day_groups(schedule),
    }
    return render(request, "lessons/lesson_list.html", context)


def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """Страница одного занятия (lesson_id — номер в расписании с 1)."""
    schedule = load_schedule()
    lesson = schedule.find_lesson_by_id(lesson_id)
    context = {"lesson_id": lesson_id, "lesson": None}
    if lesson is not None:
        context["lesson"] = build_lesson_item(schedule, lesson)
        context["day_status"] = get_day_status(
            lesson.day, timezone.localdate())
    return render(request, "lessons/lesson_detail.html", context,
                  status=404 if lesson is None else 200)
