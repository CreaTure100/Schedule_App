"""Класс «Расписание» — коллекция занятий."""

from collections.abc import Iterable, Iterator
from typing import Any, TypeVar

from models.lesson import Lesson
from models.room import Room
from models.teacher import Teacher

T = TypeVar("T")


class Schedule:
    """Расписание: упорядоченная коллекция объектов Lesson.

    Следит за тем, чтобы одинаковые преподаватели и аудитории были
    одним и тем же объектом (см. get_teacher и get_room).

    Идентификатор (ID) занятия, преподавателя или аудитории — их номер
    в соответствующем списке, начиная с 1 (так же занятия нумеруются в
    консольном меню). ID не хранится в JSON и может измениться после
    удаления занятий.
    """

    def __init__(self, lessons: Iterable[Lesson] | None = None) -> None:
        """Создать расписание, опционально сразу с занятиями."""
        self._lessons: list[Lesson] = []
        if lessons is not None:
            for lesson in lessons:
                self.add(lesson)

    @property
    def lessons(self) -> list[Lesson]:
        """Копия списка занятий (внутренний список снаружи не меняется)."""
        return list(self._lessons)

    @property
    def teachers(self) -> list[Teacher]:
        """Уникальные преподаватели в порядке появления."""
        return list(dict.fromkeys(item.teacher for item in self._lessons))

    @property
    def rooms(self) -> list[Room]:
        """Уникальные аудитории в порядке появления."""
        return list(dict.fromkeys(item.room for item in self._lessons))

    def add(self, lesson: Lesson) -> None:
        """Добавить занятие в конец расписания."""
        self._lessons.append(lesson)

    def pop(self, index: int) -> Lesson:
        """Удалить и вернуть занятие по индексу (IndexError, если нет)."""
        return self._lessons.pop(index)

    def get_teacher(self, name: str) -> Teacher:
        """Вернуть известного преподавателя или создать нового."""
        for lesson in self._lessons:
            if lesson.teacher.matches(name):
                return lesson.teacher
        return Teacher(name)

    def get_room(self, number: str) -> Room:
        """Вернуть известную аудиторию или создать новую."""
        for lesson in self._lessons:
            if lesson.room.matches(number):
                return lesson.room
        return Room(number)

    @staticmethod
    def _find_by_id(items: list[T], item_id: int) -> T | None:
        """Элемент списка по ID (номер с 1) или None, если ID нет."""
        if 1 <= item_id <= len(items):
            return items[item_id - 1]
        return None

    def find_lesson_by_id(self, lesson_id: int) -> Lesson | None:
        """Занятие по ID (номер в расписании с 1) или None."""
        return self._find_by_id(self._lessons, lesson_id)

    def find_teacher_by_id(self, teacher_id: int) -> Teacher | None:
        """Преподаватель по ID (номер в списке teachers с 1) или None."""
        return self._find_by_id(self.teachers, teacher_id)

    def find_room_by_id(self, room_id: int) -> Room | None:
        """Аудитория по ID (номер в списке rooms с 1) или None."""
        return self._find_by_id(self.rooms, room_id)

    def lesson_id(self, lesson: Lesson) -> int:
        """ID занятия из этого расписания (ValueError, если его нет)."""
        for number, item in enumerate(self._lessons, 1):
            if item is lesson:
                return number
        raise ValueError("Занятие не входит в это расписание.")

    def teacher_id(self, teacher: Teacher) -> int:
        """ID преподавателя (ValueError, если он не ведёт занятий)."""
        try:
            return self.teachers.index(teacher) + 1
        except ValueError:
            raise ValueError(
                f"Преподаватель «{teacher}» не найден.") from None

    def room_id(self, room: Room) -> int:
        """ID аудитории (ValueError, если в ней нет занятий)."""
        try:
            return self.rooms.index(room) + 1
        except ValueError:
            raise ValueError(f"Аудитория «{room}» не найдена.") from None

    def lessons_of_teacher(self, teacher: Teacher) -> list[Lesson]:
        """Занятия, которые ведёт преподаватель (в порядке расписания)."""
        return [item for item in self._lessons if item.teacher == teacher]

    def lessons_in_room(self, room: Room) -> list[Lesson]:
        """Занятия, проходящие в аудитории (в порядке расписания)."""
        return [item for item in self._lessons if item.room == room]

    def add_from_dict(self, data: dict[str, Any]) -> Lesson:
        """Создать занятие из словаря ПР2, восстановив ссылки, и добавить."""
        teacher = self.get_teacher(str(data["teacher"]))
        room = self.get_room(str(data["room"]))
        lesson = Lesson.from_dict(data, teacher, room)
        self.add(lesson)
        return lesson

    @classmethod
    def from_dicts(cls, items: Iterable[dict[str, Any]]) -> "Schedule":
        """Список словарей → расписание (при ошибке в записи — исключение)."""
        schedule = cls()
        for item in items:
            schedule.add_from_dict(item)
        return schedule

    def to_dicts(self) -> list[dict[str, str]]:
        """Расписание → список словарей, готовый для записи в JSON."""
        return [lesson.to_dict() for lesson in self._lessons]

    def __len__(self) -> int:
        """Количество занятий."""
        return len(self._lessons)

    def __iter__(self) -> Iterator[Lesson]:
        """Итерация по занятиям."""
        return iter(self._lessons)

    def __getitem__(self, index: int) -> Lesson:
        """Занятие по индексу."""
        return self._lessons[index]

    def __str__(self) -> str:
        """Нумерованный список занятий или сообщение о пустом расписании."""
        if not self._lessons:
            return "Расписание пусто."
        return "\n".join(f"{number}. {lesson}"
                         for number, lesson in enumerate(self._lessons, 1))
