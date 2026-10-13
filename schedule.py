"""Функции работы с расписанием занятий (объектная модель).

Логика, относящаяся к одному занятию, находится в методах класса Lesson.
Здесь — операции над коллекциями занятий.
"""

from collections.abc import Iterable
from datetime import date

from models import Lesson, Schedule


def add_lesson(schedule: Schedule,
               day: str, time: str, subject: str,
               teacher: str, room: str) -> Lesson:
    """Создать занятие, добавить в расписание и вернуть его.

    Преподаватель и аудитория передаются строками, как в ПР2; если такие
    уже есть в расписании, занятие получает ссылки на те же объекты.
    Некорректные данные приводят к ValueError (расписание не меняется).
    """
    lesson = Lesson(day, time, subject,
                    schedule.get_teacher(teacher),
                    schedule.get_room(room))
    schedule.add(lesson)
    return lesson


def find_lessons(lessons: Iterable[Lesson], query: str) -> list[Lesson]:
    """Найти занятия по подстроке в предмете (без учёта регистра)."""
    return [lesson for lesson in lessons if lesson.matches_subject(query)]


def filter_lessons_by_day(lessons: Iterable[Lesson],
                          day: str) -> list[Lesson]:
    """Отобрать занятия на указанный день недели."""
    return [lesson for lesson in lessons if lesson.is_on_day(day)]


def sort_lessons_by_time(lessons: Iterable[Lesson]) -> list[Lesson]:
    """Вернуть занятия, отсортированные по времени начала."""
    return sorted(lessons, key=lambda lesson: lesson.start_minutes)


def delete_lesson(schedule: Schedule, index: int) -> Lesson | None:
    """Удалить занятие по индексу. Вернуть удалённое или None."""
    if 0 <= index < len(schedule):
        return schedule.pop(index)
    return None


def get_day_status(day: str, today: date) -> str:
    """Вернуть статус дня — функция, перенесённая из ПР1."""
    weekend = ("Суббота", "Воскресенье")
    if day in weekend:
        return "Выходной — занятия не проводятся"
    if day == "Понедельник" and today.weekday() == 0:
        return "Начало недели, проверьте расписание"
    return "Учебный день"
