"""Страницы, данные которых читаются из SQLite (ПР7).

Django ORM здесь не используется: каждая view открывает соединение
стандартным модулем sqlite3, выполняет SELECT, забирает строки и
закрывает соединение. Значения от пользователя передаются в запрос
только параметрами «?», а HTML строится шаблонами через render().
"""

import sqlite3

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from db.database import unicode_lower
from models import DAYS

DB_NOT_READY = ("База данных пуста или не создана. Выполните команду "
                "python -m db.import_json и обновите страницу.")

# Общая часть: занятия вместе с названиями предмета, преподавателя и
# аудитории (JOIN четырёх таблиц).
LESSONS_SELECT = """
SELECT l.id, l.day, l.start_time, s.title AS subject, l.lesson_type,
       t.full_name AS teacher, r.number AS room
FROM lessons AS l
JOIN subjects AS s ON s.id = l.subject_id
JOIN teachers AS t ON t.id = l.teacher_id
JOIN rooms AS r ON r.id = l.room_id
"""

LESSONS_QUERY = LESSONS_SELECT + "ORDER BY l.day_number, l.start_time"

TEACHERS_QUERY = """
SELECT id, full_name, surname, email
FROM teachers
ORDER BY surname, full_name
"""

TODAY_QUERY = LESSONS_SELECT + """
WHERE l.day_number = ? AND l.start_time >= ?
ORDER BY l.start_time
"""

# Пустая строка ('') означает «критерий не задан». Символ «\» — escape для
# LIKE: «%» и «_», введённые пользователем, ищутся как обычные символы.
SEARCH_QUERY = LESSONS_SELECT + """
WHERE (? = '' OR l.day = ?)
  AND (? = '' OR lower(t.full_name) LIKE '%' || lower(?) || '%' ESCAPE '\\')
ORDER BY l.day_number, l.start_time
"""

STATS_SUMMARY_QUERY = """
SELECT COUNT(*) AS lessons_count,
       COUNT(DISTINCT teacher_id) AS teachers_count,
       COUNT(DISTINCT room_id) AS rooms_count,
       SUM(duration_hours) AS total_hours,
       MIN(start_time) AS first_start,
       MAX(start_time) AS last_start
FROM lessons
"""

STATS_BY_TEACHER_QUERY = """
SELECT t.full_name AS teacher,
       COUNT(*) AS lessons_count,
       SUM(l.duration_hours) AS hours
FROM lessons AS l
JOIN teachers AS t ON t.id = l.teacher_id
GROUP BY t.id, t.full_name
ORDER BY lessons_count DESC, t.surname
"""

STATS_BY_DAY_QUERY = """
SELECT day,
       COUNT(*) AS lessons_count,
       MIN(start_time) AS first_start,
       MAX(start_time) AS last_start
FROM lessons
GROUP BY day_number, day
ORDER BY day_number
"""

STATS_BUSY_ROOMS_QUERY = """
SELECT r.number AS room, COUNT(*) AS lessons_count
FROM lessons AS l
JOIN rooms AS r ON r.id = l.room_id
GROUP BY r.id, r.number
HAVING COUNT(*) >= 2
ORDER BY lessons_count DESC, r.number
"""


def now_local():
    """Текущее местное время (отдельная функция — чтобы подменять в тестах)."""
    return timezone.localtime()


def escape_like(text: str) -> str:
    """Экранировать «\\», «%» и «_» для LIKE ... ESCAPE '\\'."""
    return (text.replace("\\", "\\\\")
            .replace("%", "\\%").replace("_", "\\_"))


def lesson_list(request: HttpRequest) -> HttpResponse:
    """Список всех занятий: SELECT + JOIN + ORDER BY."""
    db_error = None
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        lessons = conn.execute(LESSONS_QUERY).fetchall()
    except sqlite3.OperationalError:
        lessons, db_error = [], DB_NOT_READY
    finally:
        conn.close()
    context = {"lessons": lessons, "db_error": db_error,
               "sql": LESSONS_QUERY.strip()}
    return render(request, "dbpages/lesson_list.html", context)


def teacher_list(request: HttpRequest) -> HttpResponse:
    """Список преподавателей: SELECT + ORDER BY."""
    db_error = None
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        teachers = conn.execute(TEACHERS_QUERY).fetchall()
    except sqlite3.OperationalError:
        teachers, db_error = [], DB_NOT_READY
    finally:
        conn.close()
    context = {"teachers": teachers, "db_error": db_error,
               "sql": TEACHERS_QUERY.strip()}
    return render(request, "dbpages/teacher_list.html", context)


def today_lessons(request: HttpRequest) -> HttpResponse:
    """Сегодняшние занятия, которые ещё не начались: WHERE с «?»."""
    now = now_local()
    weekday = now.isoweekday()  # 1 — понедельник ... 7 — воскресенье
    day_name = DAYS[weekday - 1] if weekday <= len(DAYS) else "Воскресенье"
    params = [weekday, now.strftime("%H:%M")]
    db_error = None
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        lessons = conn.execute(TODAY_QUERY, params).fetchall()
    except sqlite3.OperationalError:
        lessons, db_error = [], DB_NOT_READY
    finally:
        conn.close()
    context = {"lessons": lessons, "db_error": db_error,
               "day_name": day_name, "now_time": params[1],
               "sql": TODAY_QUERY.strip(), "params": params}
    return render(request, "dbpages/today.html", context)


def search_lessons(request: HttpRequest) -> HttpResponse:
    """Поиск занятий по дню недели и/или фамилии преподавателя (GET-форма)."""
    day = request.GET.get("day", "").strip()
    if day not in DAYS:
        day = ""
    teacher = request.GET.get("teacher", "").strip()
    searched = bool(day or teacher)
    lessons, db_error = [], None
    if searched:
        params = [day, day, teacher, escape_like(teacher)]
        conn = sqlite3.connect(settings.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        # lower() и LIKE в SQLite не понимают регистр кириллицы.
        conn.create_function("lower", 1, unicode_lower, deterministic=True)
        try:
            lessons = conn.execute(SEARCH_QUERY, params).fetchall()
        except sqlite3.OperationalError:
            db_error = DB_NOT_READY
        finally:
            conn.close()
    context = {"lessons": lessons, "db_error": db_error,
               "searched": searched, "day": day, "teacher": teacher,
               "days": DAYS, "sql": SEARCH_QUERY.strip()}
    return render(request, "dbpages/search.html", context)


def stats(request: HttpRequest) -> HttpResponse:
    """Статистика: агрегатные функции, GROUP BY и HAVING."""
    summary, by_teacher, by_day, busy_rooms = None, [], [], []
    db_error = None
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        summary = conn.execute(STATS_SUMMARY_QUERY).fetchone()
        by_teacher = conn.execute(STATS_BY_TEACHER_QUERY).fetchall()
        by_day = conn.execute(STATS_BY_DAY_QUERY).fetchall()
        busy_rooms = conn.execute(STATS_BUSY_ROOMS_QUERY).fetchall()
    except sqlite3.OperationalError:
        summary, db_error = None, DB_NOT_READY
    finally:
        conn.close()
    context = {
        "summary": summary, "by_teacher": by_teacher, "by_day": by_day,
        "busy_rooms": busy_rooms, "db_error": db_error,
        "sql_by_teacher": STATS_BY_TEACHER_QUERY.strip(),
        "sql_by_day": STATS_BY_DAY_QUERY.strip(),
        "sql_busy_rooms": STATS_BUSY_ROOMS_QUERY.strip(),
    }
    return render(request, "dbpages/stats.html", context)
