"""Подготовка данных занятий для шаблонов.

Модуль не формирует HTML: он превращает объекты предметной области
(Lesson, Schedule) в простые элементы со всем, что нужно шаблону —
идентификаторами для ссылок и признаком «проходит сегодня».
Так шаблонам не приходится ничего вычислять самим.
"""

from dataclasses import dataclass

from django.utils import timezone

from models import DAYS, Lesson, Schedule
from schedule import filter_lessons_by_day, sort_lessons_by_time


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


def build_lesson_item(schedule: Schedule, lesson: Lesson,
                      today: str | None = None) -> LessonItem:
    """Собрать LessonItem для одного занятия из расписания."""
    if today is None:
        today = today_name()
    return LessonItem(
        id=schedule.lesson_id(lesson),
        day=lesson.day,
        time=lesson.time,
        subject=lesson.subject,
        teacher=lesson.teacher.name,
        teacher_id=schedule.teacher_id(lesson.teacher),
        room=lesson.room.number,
        room_id=schedule.room_id(lesson.room),
        is_today=lesson.is_on_day(today),
    )


def build_lesson_items(schedule: Schedule,
                       lessons: list[Lesson]) -> list[LessonItem]:
    """Собрать LessonItem для списка занятий этого расписания."""
    today = today_name()
    return [build_lesson_item(schedule, lesson, today)
            for lesson in lessons]


def build_day_groups(schedule: Schedule) -> list[DayGroup]:
    """Занятия, сгруппированные по дням недели (Понедельник–Суббота).

    Дни идут в порядке DAYS, занятия внутри дня — по времени начала.
    Используются функции ПР3 filter_lessons_by_day() и
    sort_lessons_by_time(). Дни без занятий тоже попадают в результат.
    """
    today = today_name()
    groups = []
    for day in DAYS:
        lessons = sort_lessons_by_time(filter_lessons_by_day(schedule, day))
        groups.append(DayGroup(
            name=day,
            is_today=(day == today),
            lessons=[build_lesson_item(schedule, lesson, today)
                     for lesson in lessons],
        ))
    return groups
