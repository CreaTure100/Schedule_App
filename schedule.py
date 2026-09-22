"""Функции работы с расписанием занятий."""

from datetime import date
from typing import Any

DAYS = ["Понедельник", "Вторник", "Среда",
        "Четверг", "Пятница", "Суббота"]


def add_lesson(schedule: list[dict[str, Any]],
               day: str, time: str, subject: str,
               teacher: str, room: str) -> dict[str, Any]:
    """Добавить занятие в расписание и вернуть его."""
    lesson = {
        "day": day,
        "time": time,
        "subject": subject,
        "teacher": teacher,
        "room": room,
    }
    schedule.append(lesson)
    return lesson


def find_lessons(schedule: list[dict[str, Any]],
                 query: str) -> list[dict[str, Any]]:
    """Найти занятия по подстроке в предмете (без учёта регистра)."""
    query_lower = query.lower()
    return [lesson for lesson in schedule
            if query_lower in lesson["subject"].lower()]


def filter_lessons_by_day(schedule: list[dict[str, Any]],
                          day: str) -> list[dict[str, Any]]:
    """Отобрать занятия на указанный день недели."""
    return [lesson for lesson in schedule if lesson["day"] == day]


def sort_lessons_by_time(schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Вернуть занятия, отсортированные по времени начала."""
    return sorted(schedule, key=lambda lesson: lesson["time"])


def delete_lesson(schedule: list[dict[str, Any]], index: int) -> dict[str, Any] | None:
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
