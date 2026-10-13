"""Общие фикстуры pytest.

Файл conftest.py в корне проекта также добавляет корень в sys.path,
поэтому тесты из каталога tests/ могут импортировать модули проекта.
"""

import pytest

from models import Lesson, Room, Schedule, Teacher


@pytest.fixture
def lesson() -> Lesson:
    """Одно типовое занятие."""
    return Lesson("Понедельник", "10:00", "Математика",
                  Teacher("Иванов И.И."), Room("301"))


@pytest.fixture
def sample_schedule() -> Schedule:
    """Расписание из трёх занятий (двое занятий у одного преподавателя)."""
    schedule = Schedule()
    ivanov = Teacher("Иванов И.И.")
    room = Room("301")
    schedule.add(Lesson("Понедельник", "14:00", "Математика", ivanov, room))
    schedule.add(Lesson("Понедельник", "09:00", "Алгебра", ivanov, room))
    schedule.add(Lesson("Вторник", "12:00", "Химия",
                        Teacher("Сидоров С.С."), Room("303")))
    return schedule
