"""Подготовка данных преподавателей для шаблонов (без HTML)."""

from dataclasses import dataclass

from lessons.presenters import today_name
from models import Schedule, Teacher


@dataclass(frozen=True)
class TeacherItem:
    """Преподаватель в виде, удобном для шаблона."""

    id: int
    name: str
    surname: str
    lessons_count: int
    today_count: int


def build_teacher_item(schedule: Schedule, teacher: Teacher,
                       today: str | None = None) -> TeacherItem:
    """Собрать TeacherItem: ID, имя, число занятий и занятий сегодня."""
    if today is None:
        today = today_name()
    lessons = schedule.lessons_of_teacher(teacher)
    return TeacherItem(
        id=schedule.teacher_id(teacher),
        name=teacher.name,
        surname=teacher.surname,
        lessons_count=len(lessons),
        today_count=sum(1 for item in lessons if item.is_on_day(today)),
    )


def build_teacher_items(schedule: Schedule) -> list[TeacherItem]:
    """TeacherItem для всех преподавателей расписания."""
    today = today_name()
    return [build_teacher_item(schedule, teacher, today)
            for teacher in schedule.teachers]
