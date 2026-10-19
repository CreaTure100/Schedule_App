"""Страницы приложения «Аудитории»."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from lessons.presenters import build_lesson_items
from rooms.presenters import build_room_item, build_room_items
from storage import load_schedule


def room_list(request: HttpRequest) -> HttpResponse:
    """Список аудиторий с числом занятий в каждой."""
    schedule = load_schedule()
    context = {"rooms": build_room_items(schedule)}
    return render(request, "rooms/room_list.html", context)


def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    """Страница аудитории (room_id — номер в списке с 1)."""
    schedule = load_schedule()
    room = schedule.find_room_by_id(room_id)
    context = {"room_id": room_id, "room": None, "lessons": []}
    if room is not None:
        context["room"] = build_room_item(schedule, room)
        context["lessons"] = build_lesson_items(
            schedule, schedule.lessons_in_room(room))
    return render(request, "rooms/room_detail.html", context,
                  status=404 if room is None else 200)
