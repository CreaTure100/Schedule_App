"""Подготовка данных аудиторий для шаблонов (без HTML и без SQL)."""

from dataclasses import dataclass

from rooms.models import Room


@dataclass(frozen=True)
class RoomItem:
    """Аудитория в виде, удобном для шаблона."""

    id: int
    number: str
    floor: int | None
    capacity: int | None
    lessons_count: int
    today_count: int
    url: str = ""
    is_large: bool = False


def build_room_item(room: Room) -> RoomItem:
    """Собрать RoomItem из аудитории с аннотациями ORM.

    Объект должен быть получен запросом с annotate(lessons_count=...,
    today_count=...): число занятий считает база данных (Count).
    """
    return RoomItem(
        id=room.pk,
        number=room.number,
        floor=room.floor,
        capacity=room.capacity,
        lessons_count=room.lessons_count,
        today_count=room.today_count,
        url=room.get_absolute_url(),
        is_large=room.is_large,
    )
