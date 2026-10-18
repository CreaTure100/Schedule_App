"""Страницы приложения «Аудитории»."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from homepage.views import not_found, page
from lessons.views import lesson_list_group
from storage import load_schedule


def room_list(request: HttpRequest) -> HttpResponse:
    """Список аудиторий с числом занятий в каждой."""
    schedule = load_schedule()
    if not schedule:
        content = """
<h1 class="display-4">Аудитории</h1>
<p class="lead text-secondary">Расписание пусто.</p>
"""
        return page("Аудитории", content)
    rows = []
    for number, room in enumerate(schedule.rooms, 1):
        count = len(schedule.lessons_in_room(room))
        url = reverse("rooms:detail", args=[number])
        rows.append(f"""
  <a class="list-group-item list-group-item-action
            d-flex justify-content-between align-items-center"
     href="{url}">
    ауд. {escape(room.number)}
    <span class="badge bg-secondary">Занятий: {count}</span>
  </a>""")
    content = f"""
<h1 class="display-4">Аудитории</h1>
<div class="list-group">{''.join(rows)}
</div>
"""
    return page("Аудитории", content)


def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    """Страница аудитории (room_id — номер в списке с 1)."""
    schedule = load_schedule()
    room = schedule.find_room_by_id(room_id)
    if room is None:
        return not_found(f"Аудитория №{room_id} не найдена.")
    lessons = schedule.lessons_in_room(room)
    content = f"""
<div class="card mb-4">
  <div class="card-body">
    <h1 class="card-title display-6">Аудитория {escape(room.number)}</h1>
    <p class="card-text">Занятий в расписании: {len(lessons)}</p>
    <a class="btn btn-outline-secondary"
       href="{reverse('rooms:list')}">← Ко всем аудиториям</a>
  </div>
</div>
<h2 class="h4">Занятия в аудитории</h2>
{lesson_list_group(schedule, lessons)}
"""
    return page(f"Аудитория {room.number}", content)
