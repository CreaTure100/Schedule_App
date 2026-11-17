"""Подготовка данных преподавателей для шаблонов (без HTML и без SQL)."""

from dataclasses import dataclass

from teachers.models import Teacher


@dataclass(frozen=True)
class TeacherItem:
    """Преподаватель в виде, удобном для шаблона."""

    id: int
    name: str
    surname: str
    lessons_count: int
    today_count: int


def build_teacher_item(teacher: Teacher) -> TeacherItem:
    """Собрать TeacherItem из преподавателя с аннотациями ORM.

    Объект должен быть получен запросом с annotate(lessons_count=...,
    today_count=...): число занятий считает база данных (Count).
    """
    return TeacherItem(
        id=teacher.pk,
        name=teacher.full_name,
        surname=teacher.surname,
        lessons_count=teacher.lessons_count,
        today_count=teacher.today_count,
    )
