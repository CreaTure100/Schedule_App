"""Страницы приложения «Преподаватели»."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from homepage.views import not_found, page
from lessons.views import lesson_list_group
from storage import load_schedule


def teacher_list(request: HttpRequest) -> HttpResponse:
    """Список преподавателей с числом их занятий."""
    schedule = load_schedule()
    if not schedule:
        content = """
<h1 class="display-4">Преподаватели</h1>
<p class="lead text-secondary">Расписание пусто.</p>
"""
        return page("Преподаватели", content)
    rows = []
    for number, teacher in enumerate(schedule.teachers, 1):
        count = len(schedule.lessons_of_teacher(teacher))
        url = reverse("teachers:detail", args=[number])
        rows.append(f"""
  <a class="list-group-item list-group-item-action
            d-flex justify-content-between align-items-center"
     href="{url}">
    {escape(teacher.name)}
    <span class="badge bg-secondary">Занятий: {count}</span>
  </a>""")
    content = f"""
<h1 class="display-4">Преподаватели</h1>
<div class="list-group">{''.join(rows)}
</div>
"""
    return page("Преподаватели", content)


def teacher_detail(request: HttpRequest, teacher_id: int) -> HttpResponse:
    """Страница преподавателя (teacher_id — номер в списке с 1)."""
    schedule = load_schedule()
    teacher = schedule.find_teacher_by_id(teacher_id)
    if teacher is None:
        return not_found(f"Преподаватель №{teacher_id} не найден.")
    lessons = schedule.lessons_of_teacher(teacher)
    content = f"""
<div class="card mb-4">
  <div class="card-body">
    <h1 class="card-title display-6">{escape(teacher.name)}</h1>
    <p class="card-text">Фамилия: {escape(teacher.surname)}</p>
    <p class="card-text">Занятий в расписании: {len(lessons)}</p>
    <a class="btn btn-outline-secondary"
       href="{reverse('teachers:list')}">← Ко всем преподавателям</a>
  </div>
</div>
<h2 class="h4">Занятия преподавателя</h2>
{lesson_list_group(schedule, lessons)}
"""
    return page(teacher.name, content)
