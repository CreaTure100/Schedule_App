"""Тесты классов Teacher и Room."""

import pytest

from models import Room, Teacher


def test_teacher_attributes_and_str():
    teacher = Teacher("  Иванов И.И. ")
    assert teacher.name == "Иванов И.И."
    assert teacher.key == "Иванов И.И."
    assert str(teacher) == "Иванов И.И."


def test_teacher_surname():
    assert Teacher("Петров П.П.").surname == "Петров"


def test_teacher_empty_name_raises():
    with pytest.raises(ValueError):
        Teacher("   ")


def test_teacher_equality_and_hash():
    assert Teacher("Иванов И.И.") == Teacher("Иванов И.И.")
    assert Teacher("Иванов И.И.") != Teacher("Петров П.П.")
    assert len({Teacher("Иванов И.И."), Teacher("Иванов И.И.")}) == 1


def test_teacher_matches():
    teacher = Teacher("Иванов И.И.")
    assert teacher.matches(" Иванов И.И.")
    assert not teacher.matches("Петров П.П.")


def test_teacher_repr():
    assert repr(Teacher("Иванов И.И.")) == "Teacher('Иванов И.И.')"


def test_room_attributes_and_str():
    room = Room("301")
    assert room.number == "301"
    assert room.key == "301"
    assert str(room) == "ауд. 301"


def test_room_number_converted_to_str():
    assert Room(205).number == "205"


def test_room_empty_number_raises():
    with pytest.raises(ValueError):
        Room("")


def test_room_equality_and_hash():
    assert Room("301") == Room("301")
    assert Room("301") != Room("302")
    assert len({Room("301"), Room("301")}) == 1


def test_teacher_and_room_with_same_key_are_not_equal():
    assert Teacher("301") != Room("301")
