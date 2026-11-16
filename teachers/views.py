"""Страницы приложения «Преподаватели»."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from lessons.presenters import build_lesson_items
from roomly.data import get_schedule
from teachers.presenters import build_teacher_item, build_teacher_items


def teacher_list(request: HttpRequest) -> HttpResponse:
    """Список преподавателей с числом их занятий."""
    schedule = get_schedule()
    context = {"teachers": build_teacher_items(schedule)}
    return render(request, "teachers/teacher_list.html", context)


def teacher_detail(request: HttpRequest, teacher_id: int) -> HttpResponse:
    """Страница преподавателя (teacher_id — номер в списке с 1)."""
    schedule = get_schedule()
    teacher = schedule.find_teacher_by_id(teacher_id)
    context = {"teacher_id": teacher_id, "teacher": None, "lessons": []}
    if teacher is not None:
        context["teacher"] = build_teacher_item(schedule, teacher)
        context["lessons"] = build_lesson_items(
            schedule, schedule.lessons_of_teacher(teacher))
    return render(request, "teachers/teacher_detail.html", context,
                  status=404 if teacher is None else 200)
