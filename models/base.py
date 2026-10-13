"""Базовый класс сущностей предметной области."""

from abc import ABC, abstractmethod


class Entity(ABC):
    """Сущность, однозначно определяемая строковым ключом.

    Ключ — это именно то, что хранится в JSON (имя преподавателя или
    номер аудитории). По ключу сущности сравниваются и восстанавливаются
    при загрузке данных.
    """

    @property
    @abstractmethod
    def key(self) -> str:
        """Ключ сущности (строка, под которой она хранится в JSON)."""

    def matches(self, value: str) -> bool:
        """Проверить, соответствует ли сущность переданному ключу."""
        return self.key == value.strip()

    def __eq__(self, other: object) -> bool:
        """Сущности равны, если совпадают тип и ключ."""
        if type(self) is not type(other):
            return NotImplemented
        return self.key == other.key  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        """Хеш согласован с __eq__, поэтому сущности можно хранить в set."""
        return hash((type(self).__name__, self.key))

    def __repr__(self) -> str:
        """Техническое представление для отладки."""
        return f"{type(self).__name__}({self.key!r})"
