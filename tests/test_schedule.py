"""Тесты функций расписания."""

from datetime import date

from schedule import (
    add_lesson, find_lessons, filter_lessons_by_day,
    sort_lessons_by_time, delete_lesson, get_day_status,
)


def test_add_lesson():
    schedule = []
    add_lesson(schedule, "Понедельник", "10:00",
               "Математика", "Иванов И.И.", "301")
    assert len(schedule) == 1
    assert schedule[0]["subject"] == "Математика"


def test_find_lessons_case_insensitive():
    schedule = []
    add_lesson(schedule, "Понедельник", "10:00",
               "Математический анализ", "Иванов И.И.", "301")
    assert find_lessons(schedule, "МАТЕМАТИЧЕСКИЙ")


def test_filter_lessons_by_day():
    schedule = []
    add_lesson(schedule, "Понедельник", "10:00", "Физика", "Петров П.П.", "202")
    add_lesson(schedule, "Вторник", "12:00", "Химия", "Сидоров С.С.", "303")
    monday = filter_lessons_by_day(schedule, "Понедельник")
    assert len(monday) == 1
    assert monday[0]["subject"] == "Физика"


def test_sort_lessons_by_time():
    schedule = []
    add_lesson(schedule, "Среда", "14:00", "История", "Смирнов А.А.", "401")
    add_lesson(schedule, "Среда", "09:00", "Информатика", "Кузнецов К.К.", "402")
    sorted_lessons = sort_lessons_by_time(schedule)
    assert sorted_lessons[0]["time"] == "09:00"


def test_delete_lesson():
    schedule = []
    add_lesson(schedule, "Четверг", "11:00", "География", "Орлов О.О.", "305")
    removed = delete_lesson(schedule, 0)
    assert removed is not None
    assert len(schedule) == 0


def test_day_status_weekend():
    assert get_day_status("Суббота", date(2026, 9, 19)) == \
        "Выходной — занятия не проводятся"
