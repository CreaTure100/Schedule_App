"""Тесты класса Schedule."""

import pytest

from models import Lesson, Room, Schedule, Teacher


def test_empty_schedule():
    schedule = Schedule()
    assert len(schedule) == 0
    assert not schedule
    assert str(schedule) == "Расписание пусто."


def test_add_and_access(lesson):
    schedule = Schedule()
    schedule.add(lesson)
    assert len(schedule) == 1
    assert schedule[0] is lesson
    assert list(schedule) == [lesson]


def test_init_with_lessons(lesson):
    assert len(Schedule([lesson])) == 1


def test_lessons_property_returns_copy(sample_schedule):
    sample_schedule.lessons.clear()
    assert len(sample_schedule) == 3


def test_pop(sample_schedule):
    removed = sample_schedule.pop(0)
    assert removed.subject == "Математика"
    assert len(sample_schedule) == 2


def test_pop_bad_index_raises(sample_schedule):
    with pytest.raises(IndexError):
        sample_schedule.pop(10)


def test_get_teacher_reuses_existing_object(sample_schedule):
    first = sample_schedule[0].teacher
    assert sample_schedule.get_teacher("Иванов И.И.") is first


def test_get_teacher_creates_new(sample_schedule):
    teacher = sample_schedule.get_teacher("Новый Н.Н.")
    assert teacher == Teacher("Новый Н.Н.")


def test_get_room_reuses_existing_object(sample_schedule):
    assert sample_schedule.get_room("301") is sample_schedule[0].room


def test_get_room_creates_new(sample_schedule):
    assert sample_schedule.get_room("999") == Room("999")


def test_unique_teachers_and_rooms(sample_schedule):
    assert [t.name for t in sample_schedule.teachers] == [
        "Иванов И.И.", "Сидоров С.С."]
    assert [r.number for r in sample_schedule.rooms] == ["301", "303"]


def test_str_is_numbered_list(sample_schedule):
    lines = str(sample_schedule).splitlines()
    assert len(lines) == 3
    assert lines[0] == (
        "1. Понедельник | 14:00 | Математика | Иванов И.И. | ауд. 301")


def test_to_dicts_and_from_dicts_roundtrip(sample_schedule):
    restored = Schedule.from_dicts(sample_schedule.to_dicts())
    assert restored.lessons == sample_schedule.lessons


def test_from_dicts_shares_objects():
    data = [
        {"day": "Среда", "time": "10:00", "subject": "А",
         "teacher": "Иванов", "room": "1"},
        {"day": "Четверг", "time": "11:00", "subject": "Б",
         "teacher": "Иванов", "room": "1"},
    ]
    schedule = Schedule.from_dicts(data)
    assert schedule[0].teacher is schedule[1].teacher
    assert schedule[0].room is schedule[1].room


def test_add_from_dict_bad_data_raises():
    with pytest.raises(KeyError):
        Schedule().add_from_dict({"day": "Среда"})
    with pytest.raises(TypeError):
        Schedule().add_from_dict("не словарь")
    with pytest.raises(ValueError):
        Schedule().add_from_dict(
            {"day": "Среда", "time": "xx", "subject": "А",
             "teacher": "Т", "room": "1"})


def test_schedule_keeps_lesson_type(sample_schedule):
    assert all(isinstance(item, Lesson) for item in sample_schedule)
