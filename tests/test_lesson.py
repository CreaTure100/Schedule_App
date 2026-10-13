"""Тесты класса Lesson."""

import pytest

from models import Lesson, Room, Teacher


def test_lesson_creation(lesson):
    assert lesson.day == "Понедельник"
    assert lesson.time == "10:00"
    assert lesson.subject == "Математика"
    assert lesson.teacher == Teacher("Иванов И.И.")
    assert lesson.room.number == "301"


def test_lesson_str(lesson):
    assert str(lesson) == (
        "Понедельник | 10:00 | Математика | Иванов И.И. | ауд. 301")


def test_lesson_repr(lesson):
    assert repr(lesson) == (
        "Lesson('Понедельник', '10:00', 'Математика', "
        "Teacher('Иванов И.И.'), Room('301'))")


def test_time_is_normalized():
    lesson = Lesson("Среда", "9:05", "Физика", Teacher("А"), Room("1"))
    assert lesson.time == "09:05"


@pytest.mark.parametrize("bad_time", ["25:00", "10-00", "abc", "", "10:75"])
def test_invalid_time_raises(bad_time):
    with pytest.raises(ValueError):
        Lesson("Среда", bad_time, "Физика", Teacher("А"), Room("1"))


def test_invalid_day_raises():
    with pytest.raises(ValueError):
        Lesson("Воскресенье", "10:00", "Физика", Teacher("А"), Room("1"))


def test_empty_subject_raises():
    with pytest.raises(ValueError):
        Lesson("Среда", "10:00", "  ", Teacher("А"), Room("1"))


def test_setters_validate(lesson):
    lesson.time = "8:30"
    assert lesson.time == "08:30"
    with pytest.raises(ValueError):
        lesson.time = "99:99"
    assert lesson.time == "08:30"
    with pytest.raises(ValueError):
        lesson.day = "Фиолетовый"
    assert lesson.day == "Понедельник"


def test_parse_time_static():
    assert Lesson.parse_time("00:00") == 0
    assert Lesson.parse_time("09:30") == 570


def test_start_minutes(lesson):
    assert lesson.start_minutes == 600


def test_matches_subject_case_insensitive(lesson):
    assert lesson.matches_subject("МАТЕМ")
    assert not lesson.matches_subject("физика")


def test_is_on_day(lesson):
    assert lesson.is_on_day("Понедельник")
    assert not lesson.is_on_day("Вторник")


def test_to_dict_has_pr2_format(lesson):
    assert lesson.to_dict() == {
        "day": "Понедельник",
        "time": "10:00",
        "subject": "Математика",
        "teacher": "Иванов И.И.",
        "room": "301",
    }


def test_from_dict_roundtrip(lesson):
    restored = Lesson.from_dict(lesson.to_dict(),
                                Teacher("Иванов И.И."), Room("301"))
    assert restored == lesson


def test_from_dict_missing_key_raises(lesson):
    data = lesson.to_dict()
    del data["subject"]
    with pytest.raises(KeyError):
        Lesson.from_dict(data, lesson.teacher, lesson.room)


def test_lesson_equality(lesson):
    other = Lesson("Понедельник", "10:00", "Математика",
                   Teacher("Иванов И.И."), Room("301"))
    assert lesson == other
    other.room = Room("302")
    assert lesson != other
    assert lesson != "не занятие"
