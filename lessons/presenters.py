"""Подготовка данных занятий для шаблонов.

Модуль не формирует HTML и не обращается к базе данных: он превращает
объекты модели Lesson (их получают представления через ORM, связанные
предмет, преподаватель и аудитория загружены заранее методом
select_related) в простые элементы со всем, что нужно шаблону:
идентификаторами для ссылок и признаком «проходит сегодня».
"""

from collections.abc import Iterable
from dataclasses import dataclass

from django.utils import timezone

from lessons.models import Lesson
from models import DAYS


@dataclass(frozen=True)
class LessonItem:
    """Занятие в виде, удобном для шаблона."""

    id: int
    day: str
    time: str
    subject: str
    teacher: str
    teacher_id: int
    room: str
    room_id: int
    is_today: bool


@dataclass(frozen=True)
class DayGroup:
    """Один день недели со своими занятиями."""

    name: str
    is_today: bool
    lessons: list[LessonItem]


def today_name() -> str:
    """Название сегодняшнего дня недели ('' в воскресенье)."""
    weekday = timezone.localdate().weekday()
    return DAYS[weekday] if weekday < len(DAYS) else ""


def day_number(name: str) -> int:
    """Номер дня недели по названию: 1 — понедельник … 6 — суббота.

    Для неизвестного названия (в том числе пустого) возвращается 0:
    такого значения в базе нет, поэтому фильтр по нему ничего не найдёт.
    """
    return DAYS.index(name) + 1 if name in DAYS else 0


def today_number() -> int:
    """Номер сегодняшнего дня недели (0 в воскресенье)."""
    return day_number(today_name())


def build_lesson_item(lesson: Lesson,
                      today: str | None = None) -> LessonItem:
    """Собрать LessonItem для одного занятия из базы данных."""
    if today is None:
        today = today_name()
    day = lesson.get_day_display()
    return LessonItem(
        id=lesson.pk,
        day=day,
        time=lesson.start_time.strftime("%H:%M"),
        subject=lesson.subject_label,
        teacher=lesson.teacher.full_name,
        teacher_id=lesson.teacher_id,
        room=lesson.room.number,
        room_id=lesson.room_id,
        is_today=(day == today),
    )


def build_lesson_items(lessons: Iterable[Lesson]) -> list[LessonItem]:
    """Собрать LessonItem для набора занятий."""
    today = today_name()
    return [build_lesson_item(lesson, today) for lesson in lessons]


def build_day_groups(lessons: Iterable[Lesson]) -> list[DayGroup]:
    """Занятия, сгруппированные по дням недели (Понедельник–Суббота).

    Занятия должны прийти из базы уже отсортированными по дню и времени
    (order_by("day", "start_time")): порядок внутри дня сохраняется.
    Дни без занятий тоже попадают в результат.
    """
    today = today_name()
    by_day: dict[str, list[LessonItem]] = {day: [] for day in DAYS}
    for lesson in lessons:
        item = build_lesson_item(lesson, today)
        by_day[item.day].append(item)
    return [DayGroup(name=day, is_today=(day == today), lessons=by_day[day])
            for day in DAYS]
