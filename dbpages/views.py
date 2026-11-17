"""Страницы раздела «Статистика и поиск»: данные берутся через Django ORM.

В ПР7 эти страницы выполняли SQL-запросы через sqlite3. В ПР9 каждое
представление строит запрос методами ORM (filter, exclude, annotate,
aggregate, order_by, values, Paginator), а SQL формирует сам Django.
Текст SQL выводится на страницах для самопроверки (sql_of()).
"""

import re

from django.core.paginator import Paginator
from django.db.models import Count, F, Max, Min, Prefetch, Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from lessons.models import DAY_NAME, Lesson
from lessons.presenters import day_number
from models import DAYS
from rooms.models import Room
from teachers.models import Teacher

PAGE_SIZE = 5

# Допустимые значения параметра sort и поля сортировки ORM. Значение из
# адресной строки никогда не передаётся в order_by() напрямую: берётся
# только поле из этого словаря, неизвестное значение заменяется на "day".
SORT_FIELDS = {
    "day": ("day", "start_time"),
    "subject": ("subject__title", "day", "start_time"),
    "teacher": ("teacher__surname", "teacher__full_name", "day",
                "start_time"),
    "room": ("room__number", "day", "start_time"),
}


def now_local():
    """Текущее местное время (отдельная функция — чтобы подменять в тестах)."""
    return timezone.localtime()


def sql_of(queryset) -> str:
    """Текст SQL-запроса, который Django ORM построил для QuerySet."""
    return str(queryset.query)


def contains_nocase(field: str, text: str) -> Q:
    """Условие «поле содержит text» без учёта регистра, в том числе для
    кириллицы.

    LIKE в SQLite (а значит, и icontains) не различает регистр только у
    латиницы: «иванов» не нашло бы «Иванов». Поэтому используется
    iregex: Django выполняет его функцией REGEXP на Python, где регистр
    кириллицы учитывается верно. re.escape() делает из введённого текста
    обычную подстроку: спецсимволы («.», «%», «(») теряют особый смысл.
    """
    return Q(**{f"{field}__iregex": re.escape(text)})


def lesson_rows(queryset):
    """Занятия в виде словарей для таблицы lessons_table.html.

    annotate() добавляет вычисляемые поля: F("subject__title") берёт
    значение из связанной таблицы, DAY_NAME превращает номер дня в
    название. values() оставляет только нужные поля, поэтому select_related()
    здесь не нужен: нужные столбцы связанных таблиц уже в запросе.
    """
    return (
        queryset
        .annotate(
            day_name=DAY_NAME,
            subject_title=F("subject__title"),
            teacher_name=F("teacher__full_name"),
            room_number=F("room__number"),
        )
        .values(
            "id", "day_name", "start_time", "lesson_type",
            "subject_title", "teacher_name", "room_number",
        )
    )


def parse_id(text: str) -> int | None:
    """Целое число из параметра запроса или None, если это не число."""
    if text.isascii() and text.isdigit() and len(text) <= 9:
        return int(text)
    return None


def lesson_list(request: HttpRequest) -> HttpResponse:
    """Все занятия: фильтры, сортировка и постраничный вывод."""
    day_name = request.GET.get("day", "").strip()
    teacher_id = request.GET.get("teacher", "").strip()
    room_id = request.GET.get("room", "").strip()
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "day")
    if sort not in SORT_FIELDS:
        sort = "day"
    error = None

    lessons = Lesson.objects.all()

    # Фильтры применяются по очереди и объединяются по «И».
    if day_name:
        if day_name in DAYS:
            lessons = lessons.filter(day=day_number(day_name))
        else:
            error = "Выберите день недели из списка."
    teacher_pk, room_pk = parse_id(teacher_id), parse_id(room_id)
    if teacher_pk is not None:
        lessons = lessons.filter(teacher_id=teacher_pk)
    if room_pk is not None:
        lessons = lessons.filter(room_id=room_pk)
    if query:
        # Фильтрация по полю связанной модели (subject__title).
        lessons = lessons.filter(contains_nocase("subject__title", query))

    rows = lesson_rows(lessons.order_by(*SORT_FIELDS[sort], "pk"))

    # Пагинация применяется после фильтрации и сортировки.
    paginator = Paginator(rows, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "lessons": page_obj,
        "page_obj": page_obj,
        "total": paginator.count,
        "days": DAYS,
        "teachers": Teacher.objects.order_by("surname", "full_name"),
        "rooms": Room.objects.order_by("number"),
        "day": day_name,
        "selected_teacher": teacher_id,
        "selected_room": room_id,
        "q": query,
        "sort": sort,
        "error": error,
        "sql": sql_of(rows),
    }
    return render(request, "dbpages/lesson_list.html", context)


def teacher_list(request: HttpRequest) -> HttpResponse:
    """Список преподавателей и предметов, которые они ведут."""
    # prefetch_related() загружает занятия всех преподавателей отдельным
    # запросом (вместо запроса на каждого преподавателя); Prefetch с
    # select_related("subject") заодно подтягивает предметы.
    teachers = (
        Teacher.objects
        .order_by("surname", "full_name")
        .prefetch_related(Prefetch(
            "lessons",
            queryset=Lesson.objects.select_related("subject"),
        ))
    )
    rows = [
        {
            "id": teacher.pk,
            "full_name": teacher.full_name,
            "surname": teacher.surname,
            "email": teacher.email,
            "subjects": sorted({lesson.subject.title
                                for lesson in teacher.lessons.all()}),
        }
        for teacher in teachers
    ]
    context = {"teachers": rows, "sql": sql_of(teachers)}
    return render(request, "dbpages/teacher_list.html", context)


def today_lessons(request: HttpRequest) -> HttpResponse:
    """Сегодняшние занятия, которые ещё не начались."""
    now = now_local()
    weekday = now.isoweekday()  # 1 — понедельник ... 7 — воскресенье
    day_name = DAYS[weekday - 1] if weekday <= len(DAYS) else "Воскресенье"
    now_time = now.time().replace(second=0, microsecond=0)
    # В воскресенье day=7: такого значения в базе нет, список пуст.
    rows = lesson_rows(
        Lesson.objects
        .filter(day=weekday, start_time__gte=now_time)
        .order_by("start_time", "pk")
    )
    context = {
        "lessons": rows,
        "day_name": day_name,
        "now_time": now_time.strftime("%H:%M"),
        "sql": sql_of(rows),
    }
    return render(request, "dbpages/today.html", context)


def search_lessons(request: HttpRequest) -> HttpResponse:
    """Поиск занятий по дню, преподавателю и предмету или аудитории."""
    day_name = request.GET.get("day", "").strip()
    if day_name not in DAYS:
        day_name = ""
    teacher = request.GET.get("teacher", "").strip()
    query = request.GET.get("q", "").strip()
    searched = bool(day_name or teacher or query)

    rows, sql = [], ""
    if searched:
        lessons = Lesson.objects.all()
        if day_name:
            lessons = lessons.filter(day=day_number(day_name))
        if teacher:
            lessons = lessons.filter(
                contains_nocase("teacher__full_name", teacher))
        if query:
            # Поиск по нескольким полям: предмет ИЛИ номер аудитории.
            lessons = lessons.filter(
                contains_nocase("subject__title", query)
                | contains_nocase("room__number", query)
            )
        rows = lesson_rows(lessons.order_by("day", "start_time", "pk"))
        sql = sql_of(rows)

    context = {
        "lessons": rows,
        "searched": searched,
        "day": day_name,
        "teacher": teacher,
        "q": query,
        "days": DAYS,
        "sql": sql,
    }
    return render(request, "dbpages/search.html", context)


def stats(request: HttpRequest) -> HttpResponse:
    """Статистика: агрегирование, аннотирование и группировка."""
    # aggregate() — один сводный результат по всей таблице занятий.
    summary = Lesson.objects.aggregate(
        lessons_count=Count("id"),
        teachers_count=Count("teacher", distinct=True),
        rooms_count=Count("room", distinct=True),
        total_hours=Sum("duration_hours"),
        first_start=Min("start_time"),
        last_start=Max("start_time"),
    )

    # annotate() — показатель для каждого преподавателя. Запрос строится
    # от Teacher, поэтому преподаватели без занятий тоже в списке (0).
    by_teacher = (
        Teacher.objects
        .annotate(
            lessons_count=Count("lessons"),
            hours=Sum("lessons__duration_hours"),
        )
        .order_by("-lessons_count", "surname")
    )

    # values() + annotate() — группировка (GROUP BY day).
    by_day_query = (
        Lesson.objects
        .values("day")
        .annotate(
            lessons_count=Count("id"),
            first_start=Min("start_time"),
            last_start=Max("start_time"),
        )
        .order_by("day")
    )
    by_day = [{**row, "day_name": DAYS[row["day"] - 1]}
              for row in by_day_query]

    # Фильтр по аннотации после annotate() — аналог HAVING в SQL.
    busy_rooms = (
        Room.objects
        .annotate(lessons_count=Count("lessons"))
        .filter(lessons_count__gte=2)
        .order_by("-lessons_count", "number")
    )

    context = {
        "summary": summary,
        "by_teacher": by_teacher,
        "by_day": by_day,
        "busy_rooms": busy_rooms,
        "sql_by_teacher": sql_of(by_teacher),
        "sql_by_day": sql_of(by_day_query),
        "sql_busy_rooms": sql_of(busy_rooms),
    }
    return render(request, "dbpages/stats.html", context)
