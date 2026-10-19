"""Подготовка данных аудиторий для шаблонов (без HTML)."""

from dataclasses import dataclass

from lessons.presenters import today_name
from models import Room, Schedule


@dataclass(frozen=True)
class RoomItem:
    """Аудитория в виде, удобном для шаблона."""

    id: int
    number: str
    lessons_count: int
    today_count: int


def build_room_item(schedule: Schedule, room: Room,
                    today: str | None = None) -> RoomItem:
    """Собрать RoomItem: ID, номер, число занятий и занятий сегодня."""
    if today is None:
        today = today_name()
    lessons = schedule.lessons_in_room(room)
    return RoomItem(
        id=schedule.room_id(room),
        number=room.number,
        lessons_count=len(lessons),
        today_count=sum(1 for item in lessons if item.is_on_day(today)),
    )


def build_room_items(schedule: Schedule) -> list[RoomItem]:
    """RoomItem для всех аудиторий расписания."""
    today = today_name()
    return [build_room_item(schedule, room, today)
            for room in schedule.rooms]
