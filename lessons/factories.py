"""Вспомогательные функции для создания тестовых данных через ORM."""

from lessons.models import Lesson, Subject
from models import DAYS
from rooms.models import Room
from teachers.models import Teacher


def make_lesson(day: str, time: str, subject: str, teacher: str,
                room: str, lesson_type: str = "",
                status: str = Lesson.Status.ACTIVE) -> Lesson:
    """Создать занятие, при необходимости создав предмет, преподавателя
    и аудиторию (get_or_create не дублирует уже существующие записи).

    day — название дня («Понедельник»), time — строка «ЧЧ:ММ»,
    status — статус занятия (по умолчанию «проводится»).
    """
    return Lesson.objects.create(
        day=DAYS.index(day) + 1,
        start_time=time,
        lesson_type=lesson_type,
        status=status,
        subject=Subject.objects.get_or_create(title=subject)[0],
        teacher=Teacher.objects.get_or_create(full_name=teacher)[0],
        room=Room.objects.get_or_create(number=room)[0],
    )
