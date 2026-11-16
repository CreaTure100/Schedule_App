"""Загрузка расписания из SQLite в объекты предметной области (ПР7).

Страницы сайта получают данные отсюда. SQL-запрос с JOIN собирает
строки таблиц, а затем они превращаются в те же объекты Lesson,
Teacher и Room (пакет models/) и в Schedule, с которыми страницы
работали, пока читали JSON. Поэтому презентеры и шаблоны не менялись.
"""

import sqlite3
from pathlib import Path

from db.database import DB_PATH, get_connection
from models import Schedule

# ORDER BY l.id сохраняет порядок, в котором занятия были импортированы
# из JSON: номера занятий, преподавателей и аудиторий на сайте (они
# считаются по порядку появления) остаются прежними.
SCHEDULE_QUERY = """
SELECT l.day, l.start_time, s.title, l.lesson_type,
       t.full_name AS teacher, r.number AS room
FROM lessons AS l
JOIN subjects AS s ON s.id = l.subject_id
JOIN teachers AS t ON t.id = l.teacher_id
JOIN rooms AS r ON r.id = l.room_id
ORDER BY l.id
"""

HINT = "Выполните команду: python -m db.import_json"


def subject_name(title: str, lesson_type: str | None) -> str:
    """Собрать название предмета из таблиц: «Химия» + «лабораторная»."""
    return f"{title} ({lesson_type})" if lesson_type else title


def load_schedule_from_db(db_path: str | Path | None = None) -> Schedule:
    """Прочитать расписание из базы: SQL → строки → объекты Lesson.

    Если базы нет или в ней нет таблиц, возвращается пустое расписание
    (как и при чтении отсутствующего JSON-файла).
    """
    path = Path(db_path or DB_PATH)
    if not path.exists():
        print(f"База данных {path} не найдена. {HINT}")
        return Schedule()
    conn = get_connection(path)
    try:
        rows = conn.execute(SCHEDULE_QUERY).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"Не удалось прочитать базу {path}: {exc}. {HINT}")
        return Schedule()
    finally:
        conn.close()

    schedule = Schedule()
    for number, row in enumerate(rows, 1):
        try:
            schedule.add_from_dict({
                "day": row["day"],
                "time": row["start_time"],
                "subject": subject_name(row["title"], row["lesson_type"]),
                "teacher": row["teacher"],
                "room": row["room"],
            })
        except (KeyError, TypeError, ValueError) as exc:
            print(f"Запись №{number} пропущена "
                  f"({type(exc).__name__}: {exc}).")
    return schedule
