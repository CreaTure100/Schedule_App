"""Тесты функций расписания (ПР2, адаптированы под объектную модель)."""

from datetime import date

import pytest

from models import Lesson, Schedule
from schedule import (
    add_lesson, find_lessons, filter_lessons_by_day,
    sort_lessons_by_time, delete_lesson, get_day_status,
)


def test_add_lesson():
    schedule = Schedule()
    lesson = add_lesson(schedule, "Понедельник", "10:00",
                        "Математика", "Иванов И.И.", "301")
    assert len(schedule) == 1
    assert isinstance(lesson, Lesson)
    assert schedule[0].subject == "Математика"
    assert schedule[0].teacher.name == "Иванов И.И."
    assert schedule[0].room.number == "301"


def test_add_lesson_shares_teacher_and_room():
    schedule = Schedule()
    add_lesson(schedule, "Понедельник", "10:00", "А", "Иванов", "301")
    add_lesson(schedule, "Вторник", "10:00", "Б", "Иванов", "301")
    assert schedule[0].teacher is schedule[1].teacher
    assert schedule[0].room is schedule[1].room


def test_add_lesson_invalid_time_does_not_change_schedule():
    schedule = Schedule()
    with pytest.raises(ValueError):
        add_lesson(schedule, "Понедельник", "25:00", "А", "Иванов", "301")
    assert len(schedule) == 0


def test_find_lessons_case_insensitive():
    schedule = Schedule()
    add_lesson(schedule, "Понедельник", "10:00",
               "Математический анализ", "Иванов И.И.", "301")
    assert find_lessons(schedule, "МАТЕМАТИЧЕСКИЙ")


def test_find_lessons_nothing_found(sample_schedule):
    assert find_lessons(sample_schedule, "Биология") == []


def test_find_lessons_accepts_plain_list(sample_schedule):
    assert len(find_lessons(sample_schedule.lessons, "алгебра")) == 1


def test_filter_lessons_by_day():
    schedule = Schedule()
    add_lesson(schedule, "Понедельник", "10:00", "Физика",
               "Петров П.П.", "202")
    add_lesson(schedule, "Вторник", "12:00", "Химия",
               "Сидоров С.С.", "303")
    monday = filter_lessons_by_day(schedule, "Понедельник")
    assert len(monday) == 1
    assert monday[0].subject == "Физика"


def test_sort_lessons_by_time():
    schedule = Schedule()
    add_lesson(schedule, "Среда", "14:00", "История",
               "Смирнов А.А.", "401")
    add_lesson(schedule, "Среда", "09:00", "Информатика",
               "Кузнецов К.К.", "402")
    sorted_lessons = sort_lessons_by_time(schedule)
    assert sorted_lessons[0].time == "09:00"
    # исходное расписание не изменилось
    assert schedule[0].subject == "История"


def test_sort_handles_single_digit_hour():
    schedule = Schedule()
    add_lesson(schedule, "Среда", "10:00", "А", "Т", "1")
    add_lesson(schedule, "Среда", "9:00", "Б", "Т", "1")
    assert [x.subject for x in sort_lessons_by_time(schedule)] == ["Б", "А"]


def test_delete_lesson():
    schedule = Schedule()
    add_lesson(schedule, "Четверг", "11:00", "География",
               "Орлов О.О.", "305")
    removed = delete_lesson(schedule, 0)
    assert removed is not None
    assert removed.subject == "География"
    assert len(schedule) == 0


def test_delete_lesson_bad_index_returns_none(sample_schedule):
    assert delete_lesson(sample_schedule, 5) is None
    assert delete_lesson(sample_schedule, -1) is None
    assert len(sample_schedule) == 3


def test_day_status_weekend():
    assert get_day_status("Суббота", date(2026, 9, 19)) == \
        "Выходной — занятия не проводятся"


def test_day_status_monday():
    assert get_day_status("Понедельник", date(2026, 9, 21)) == \
        "Начало недели, проверьте расписание"


def test_day_status_working_day():
    assert get_day_status("Среда", date(2026, 9, 23)) == "Учебный день"
