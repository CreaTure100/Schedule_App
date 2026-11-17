"""Страницы приложения «Преподаватели»: данные берутся через Django ORM."""

from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from lessons import presenters as lesson_presenters
from lessons.models import Lesson
from teachers.models import Teacher
from teachers.presenters import build_teacher_item


def teachers_with_counts():
    """Преподаватели с числом занятий всего и на сегодня.

    Count("lessons") считает занятия по обратной связи related_name;
    Count(..., filter=Q(...)) — только занятия сегодняшнего дня.
    Запрос строится от Teacher, поэтому преподаватели без занятий
    остаются в результате (счётчик равен 0).
    """
    today = lesson_presenters.today_number()
    # ПР11: отменённые занятия не считаются.
    active = Q(lessons__status=Lesson.Status.ACTIVE)
    return Teacher.objects.annotate(
        lessons_count=Count("lessons", filter=active),
        today_count=Count("lessons", filter=active & Q(lessons__day=today)),
    )


def teacher_list(request: HttpRequest) -> HttpResponse:
    """Список преподавателей с числом их занятий."""
    teachers = teachers_with_counts().order_by("surname", "full_name")
    context = {"teachers": [build_teacher_item(item) for item in teachers]}
    return render(request, "teachers/teacher_list.html", context)


def teacher_detail(request: HttpRequest, teacher_id: int) -> HttpResponse:
    """Страница преподавателя (teacher_id — первичный ключ записи)."""
    teacher = get_object_or_404(teachers_with_counts(), pk=teacher_id)
    # Обратная связь: занятия преподавателя через related_name="lessons".
    lessons = teacher.lessons.active().select_related("subject", "room")
    context = {
        "teacher": build_teacher_item(teacher),
        "lessons": lesson_presenters.build_lesson_items(lessons),
    }
    return render(request, "teachers/teacher_detail.html", context)
