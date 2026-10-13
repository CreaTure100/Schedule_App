"""Класс «Занятие»."""

from datetime import datetime
from typing import Any

from models.room import Room
from models.teacher import Teacher

DAYS = ["Понедельник", "Вторник", "Среда",
        "Четверг", "Пятница", "Суббота"]
TIME_FORMAT = "%H:%M"


class Lesson:
    """Занятие: день, время, предмет, преподаватель и аудитория.

    Преподаватель и аудитория хранятся как ссылки на объекты
    Teacher и Room
    """

    def __init__(self, day: str, time: str, subject: str,
                 teacher: Teacher, room: Room) -> None:
        """Создать занятие. Некорректные день, время и предмет → ValueError."""
        self.day = day
        self.time = time
        self.subject = subject
        self.teacher = teacher
        self.room = room

    @staticmethod
    def parse_time(time: str) -> int:
        """Преобразовать «ЧЧ:ММ» в число минут от начала суток."""
        try:
            parsed = datetime.strptime(time.strip(), TIME_FORMAT)
        except ValueError:
            raise ValueError(
                f"Неверное время «{time}». Ожидается ЧЧ:ММ, "
                f"например 09:30.") from None
        return parsed.hour * 60 + parsed.minute

    @property
    def day(self) -> str:
        """День недели (одно из значений DAYS)."""
        return self._day

    @day.setter
    def day(self, value: str) -> None:
        value = value.strip()
        if value not in DAYS:
            raise ValueError(f"Неизвестный день недели: «{value}».")
        self._day = value

    @property
    def time(self) -> str:
        """Время начала в нормализованном виде «ЧЧ:ММ»."""
        return self._time

    @time.setter
    def time(self, value: str) -> None:
        minutes = self.parse_time(value)
        self._time = f"{minutes // 60:02d}:{minutes % 60:02d}"

    @property
    def subject(self) -> str:
        """Название предмета."""
        return self._subject

    @subject.setter
    def subject(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Название предмета не может быть пустым.")
        self._subject = value

    @property
    def start_minutes(self) -> int:
        """Время начала в минутах от начала суток (для сортировки)."""
        return self.parse_time(self._time)

    def matches_subject(self, query: str) -> bool:
        """Содержится ли подстрока в названии предмета (без регистра)."""
        return query.lower() in self._subject.lower()

    def is_on_day(self, day: str) -> bool:
        """Проходит ли занятие в указанный день недели."""
        return self._day == day

    def to_dict(self) -> dict[str, str]:
        """Объект → словарь в формате ПР2 (связи хранятся ключами)."""
        return {
            "day": self._day,
            "time": self._time,
            "subject": self._subject,
            "teacher": self.teacher.key,
            "room": self.room.key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any],
                  teacher: Teacher, room: Room) -> "Lesson":
        """Словарь → объект; преподаватель и аудитория уже найдены."""
        return cls(str(data["day"]), str(data["time"]),
                   str(data["subject"]), teacher, room)

    def __str__(self) -> str:
        """Строка: день | время | предмет | преподаватель | аудитория."""
        return (f"{self._day} | {self._time} | {self._subject} | "
                f"{self.teacher} | {self.room}")

    def __repr__(self) -> str:
        """Техническое представление для отладки."""
        return (f"Lesson({self._day!r}, {self._time!r}, "
                f"{self._subject!r}, {self.teacher!r}, {self.room!r})")

    def __eq__(self, other: object) -> bool:
        """Занятия равны, если равны все их поля."""
        if not isinstance(other, Lesson):
            return NotImplemented
        return (self._day, self._time, self._subject,
                self.teacher, self.room) == (
            other._day, other._time, other._subject,
            other.teacher, other.room)
