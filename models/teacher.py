"""Класс «Преподаватель»."""

from models.base import Entity


class Teacher(Entity):
    """Преподаватель, ведущий занятия."""

    def __init__(self, name: str) -> None:
        """Создать преподавателя; имя не может быть пустым."""
        name = name.strip()
        if not name:
            raise ValueError("Имя преподавателя не может быть пустым.")
        self._name = name

    @property
    def name(self) -> str:
        """Имя преподавателя (например, «Иванов И.И.»)."""
        return self._name

    @property
    def key(self) -> str:
        """Ключ для JSON — имя преподавателя."""
        return self._name

    @property
    def surname(self) -> str:
        """Фамилия — первое слово имени."""
        return self._name.split()[0]

    def __str__(self) -> str:
        """Строковое представление: имя преподавателя."""
        return self._name
