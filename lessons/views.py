"""Страницы приложения «Занятия»: данные берутся через Django ORM."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from lessons import presenters
from lessons.models import Lesson
from schedule import get_day_status


def lesson_list(request: HttpRequest) -> HttpResponse:
    """Список занятий, сгруппированных по дням недели."""
    # select_related() подтягивает предмет, преподавателя и аудиторию
    # тем же запросом (JOIN), а order_by() сортирует по дню и времени:
    # вся страница строится одним обращением к базе данных.
    lessons = list(
        Lesson.objects
        .with_related()
        .order_by("day", "start_time", "pk")
    )
    context = {
        "lessons": presenters.build_lesson_items(lessons),
        "days": presenters.build_day_groups(lessons),
    }
    return render(request, "lessons/lesson_list.html", context)


def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """Страница одного занятия (lesson_id — первичный ключ записи)."""
    # Если записи нет, get_object_or_404() вызывает Http404, и Django
    # показывает страницу 404 (handler404) без необработанного исключения.
    lesson = get_object_or_404(
        Lesson.objects.select_related("subject", "teacher", "room"),
        pk=lesson_id,
    )
    context = {
        "lesson": presenters.build_lesson_item(lesson),
        "day_status": get_day_status(
            lesson.get_day_display(), timezone.localdate()),
    }
    return render(request, "lessons/lesson_detail.html", context)
