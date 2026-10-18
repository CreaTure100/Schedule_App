"""Страницы приложения «Занятия»."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from homepage.views import not_found, page
from models import DAYS, Lesson, Schedule
from schedule import get_day_status
from storage import load_schedule


def today_name() -> str:
    """Название сегодняшнего дня недели ('' в воскресенье)."""
    weekday = timezone.localdate().weekday()
    return DAYS[weekday] if weekday < len(DAYS) else ""


def day_badge(lesson: Lesson) -> str:
    """Бейдж с днём недели; зелёный, если занятие проходит сегодня."""
    day = escape(lesson.day)
    if lesson.is_on_day(today_name()):
        return f'<span class="badge bg-success">{day}, сегодня</span>'
    return f'<span class="badge bg-secondary">{day}</span>'


def lesson_list_group(schedule: Schedule, lessons: list[Lesson]) -> str:
    """HTML-список занятий со ссылками на страницы занятий.

    Используется также в приложениях teachers и rooms.
    """
    rows = []
    for lesson in lessons:
        url = reverse("lessons:detail", args=[schedule.lesson_id(lesson)])
        rows.append(f"""
  <a class="list-group-item list-group-item-action
            d-flex justify-content-between align-items-center"
     href="{url}">
    <span>
      <strong>{escape(lesson.subject)}</strong><br>
      <small class="text-secondary">{lesson.time} ·
        {escape(lesson.teacher.name)} ·
        ауд. {escape(lesson.room.number)}</small>
    </span>
    {day_badge(lesson)}
  </a>""")
    return f'<div class="list-group">{''.join(rows)}\n</div>'


def lesson_list(request: HttpRequest) -> HttpResponse:
    """Список всех занятий в порядке расписания."""
    schedule = load_schedule()
    if not schedule:
        content = """
<h1 class="display-4">Занятия</h1>
<p class="lead text-secondary">Расписание пусто.</p>
"""
        return page("Занятия", content)
    content = f"""
<h1 class="display-4">Занятия</h1>
<p class="lead">Всего занятий: {len(schedule)}</p>
{lesson_list_group(schedule, schedule.lessons)}
"""
    return page("Занятия", content)


def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """Страница одного занятия (lesson_id — номер в расписании с 1)."""
    schedule = load_schedule()
    lesson = schedule.find_lesson_by_id(lesson_id)
    if lesson is None:
        return not_found(f"Занятие №{lesson_id} не найдено.")
    teacher_url = reverse(
        "teachers:detail", args=[schedule.teacher_id(lesson.teacher)])
    room_url = reverse("rooms:detail", args=[schedule.room_id(lesson.room)])
    status = get_day_status(lesson.day, timezone.localdate())
    content = f"""
<div class="card">
  <div class="card-body">
    <h1 class="card-title display-6">{escape(lesson.subject)}</h1>
    <p>{day_badge(lesson)}</p>
    <p class="card-text">Время начала: <strong>{lesson.time}</strong></p>
    <p class="card-text">Преподаватель:
      <a href="{teacher_url}">{escape(lesson.teacher.name)}</a></p>
    <p class="card-text">Аудитория:
      <a href="{room_url}">ауд. {escape(lesson.room.number)}</a></p>
    <p class="card-text">Статус дня: {escape(status)}</p>
    <a class="btn btn-outline-secondary"
       href="{reverse('lessons:list')}">← Ко всем занятиям</a>
  </div>
</div>
"""
    return page(lesson.subject, content)
