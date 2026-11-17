"""Страницы приложения «Аудитории»: данные берутся через Django ORM."""

from datetime import datetime

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from lessons import presenters as lesson_presenters
from lessons.models import Lesson
from models import DAYS
from rooms.forms import RoomForm
from rooms.models import Room
from rooms.presenters import build_room_item


def rooms_with_counts():
    """Аудитории с числом занятий всего и на сегодня.

    Запрос строится от Room, поэтому аудитории без занятий не пропадают
    из результата (аналог LEFT JOIN): для них счётчики равны 0.
    """
    today = lesson_presenters.today_number()
    # ПР11: отменённые занятия не считаются.
    active = Q(lessons__status=Lesson.Status.ACTIVE)
    return Room.objects.annotate(
        lessons_count=Count("lessons", filter=active),
        today_count=Count("lessons", filter=active & Q(lessons__day=today)),
    )


def room_list(request: HttpRequest) -> HttpResponse:
    """Список аудиторий с числом занятий в каждой."""
    rooms = rooms_with_counts().order_by("number")
    context = {"rooms": [build_room_item(item) for item in rooms]}
    return render(request, "rooms/room_list.html", context)


def render_room(request: HttpRequest, room: Room) -> HttpResponse:
    """Общая часть страниц аудитории: по первичному ключу и по slug."""
    # Обратная связь: занятия аудитории через related_name="lessons".
    lessons = room.lessons.active().select_related("subject", "teacher")
    context = {
        "room": build_room_item(room),
        "lessons": lesson_presenters.build_lesson_items(lessons),
    }
    return render(request, "rooms/room_detail.html", context)


def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    """Страница аудитории (room_id — первичный ключ записи)."""
    room = get_object_or_404(rooms_with_counts(), pk=room_id)
    return render_room(request, room)


def room_detail_by_slug(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница аудитории по slug: /rooms/auditoriya-301-1/.

    Если аудитории с таким slug нет, get_object_or_404() вызывает Http404
    (страница 404), а не необработанное исключение DoesNotExist.
    """
    room = get_object_or_404(rooms_with_counts(), slug=slug)
    return render_room(request, room)


def free_rooms(request: HttpRequest) -> HttpResponse:
    """Поиск свободных аудиторий на выбранные день и время начала.

    Аудитория свободна, если в этот день в это время в ней не начинается
    ни одно занятие.
    """
    day_name = request.GET.get("day", "").strip()
    time_text = request.GET.get("time", "").strip()
    searched = bool(day_name or time_text)
    rooms, error = [], None

    if searched:
        if day_name not in DAYS:
            error = "Выберите день недели."
        else:
            try:
                start_time = datetime.strptime(time_text, "%H:%M").time()
            except ValueError:
                error = "Укажите время начала в формате ЧЧ:ММ."
            else:
                # Идентификаторы аудиторий, занятых в этот день и время.
                # Отменённое занятие аудиторию не занимает.
                busy_room_ids = Lesson.objects.active().at(
                    lesson_presenters.day_number(day_name),
                    start_time,
                ).values_list("room_id", flat=True)
                # Все остальные аудитории свободны.
                rooms = Room.objects.exclude(
                    pk__in=busy_room_ids,
                ).order_by("number")

    context = {
        "rooms": rooms,
        "days": DAYS,
        "day": day_name,
        "time": time_text,
        "searched": searched,
        "error": error,
    }
    return render(request, "rooms/free_rooms.html", context)


def room_create(request: HttpRequest) -> HttpResponse:
    """Добавление аудитории с изображением (ПР11).

    В форму передаются и request.POST, и request.FILES: без FILES
    загруженный файл до формы не дойдёт.
    """
    if request.method == "POST":
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save()
            messages.success(request, "Аудитория добавлена.")
            return redirect(room)
    else:
        form = RoomForm()
    return render(request, "rooms/room_form.html", {"form": form})


def room_update(request: HttpRequest, room_id: int) -> HttpResponse:
    """Редактирование аудитории и замена изображения (ПР11)."""
    room = get_object_or_404(Room, pk=room_id)
    if request.method == "POST":
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            room = form.save()
            messages.success(request, "Изменения сохранены.")
            return redirect(room)
    else:
        form = RoomForm(instance=room)
    context = {"form": form, "room_id": room_id}
    return render(request, "rooms/room_form.html", context)
