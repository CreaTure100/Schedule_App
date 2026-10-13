"""Класс «Аудитория»."""

from models.base import Entity


class Room(Entity):
    """Аудитория, в которой проходят занятия."""

    def __init__(self, number: str) -> None:
        """Создать аудиторию; номер хранится строкой («301», «12а»)."""
        number = str(number).strip()
        if not number:
            raise ValueError("Номер аудитории не может быть пустым.")
        self._number = number

    @property
    def number(self) -> str:
        """Номер аудитории."""
        return self._number

    @property
    def key(self) -> str:
        """Ключ для JSON — номер аудитории."""
        return self._number

    def __str__(self) -> str:
        """Строковое представление: «ауд. 301»."""
        return f"ауд. {self._number}"
