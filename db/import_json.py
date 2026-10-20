"""Перенос данных из data/schedule.json в базу SQLite (ПР7).

Запуск из корня проекта:

    python -m db.import_json [путь_к_json]

JSON читается через storage.load_schedule(): данные проходят ту же
проверку и нормализацию, что и в ПР3 (дни недели, формат времени).
Повторный запуск безопасен: уже существующие строки не дублируются.
"""

import re
import sqlite3
import sys
from pathlib import Path

from db.database import BASE_DIR, get_connection, init_db
from models import DAYS, Schedule
from storage import load_schedule

DEFAULT_JSON = BASE_DIR / "data" / "schedule.json"

# «Химия (лабораторная)» -> название «Химия», тип «лабораторная».
SUBJECT_TYPE_RE = re.compile(r"^(?P<title>.+?)\s*\((?P<kind>[^()]+)\)\s*$")

# Все значения подставляются через «?», а не через f-строки.
INSERT_TEACHER = (
    "INSERT INTO teachers (full_name, surname) VALUES (?, ?) "
    "ON CONFLICT DO NOTHING"
)
INSERT_ROOM = (
    "INSERT INTO rooms (number, floor) VALUES (?, ?) "
    "ON CONFLICT DO NOTHING"
)
INSERT_SUBJECT = (
    "INSERT INTO subjects (title) VALUES (?) ON CONFLICT DO NOTHING"
)
# Внешние ключи находятся подзапросами по естественному ключу из JSON.
INSERT_LESSON = (
    "INSERT INTO lessons "
    "(day, day_number, start_time, lesson_type, "
    "subject_id, teacher_id, room_id) "
    "VALUES (?, ?, ?, ?, "
    "(SELECT id FROM subjects WHERE title = ?), "
    "(SELECT id FROM teachers WHERE full_name = ?), "
    "(SELECT id FROM rooms WHERE number = ?)) "
    "ON CONFLICT DO NOTHING"
)


def split_subject(subject: str) -> tuple[str, str | None]:
    """Разделить предмет на название и необязательный тип занятия."""
    match = SUBJECT_TYPE_RE.match(subject)
    if match is None:
        return subject, None
    return match["title"], match["kind"].strip().lower()


def room_floor(number: str) -> int | None:
    """Этаж — первая цифра числового номера из трёх и более цифр."""
    if number.isdigit() and len(number) >= 3:
        return int(number[0])
    return None


def build_rows(schedule: Schedule) -> dict[str, list[tuple]]:
    """Подготовить кортежи параметров для executemany()."""
    teachers = [(t.name, t.surname) for t in schedule.teachers]
    rooms = [(r.number, room_floor(r.number)) for r in schedule.rooms]
    subjects: list[tuple[str]] = []
    lessons = []
    for lesson in schedule:
        title, kind = split_subject(lesson.subject)
        if (title,) not in subjects:
            subjects.append((title,))
        lessons.append((
            lesson.day, DAYS.index(lesson.day) + 1, lesson.time, kind,
            title, lesson.teacher.name, lesson.room.number,
        ))
    return {"teachers": teachers, "rooms": rooms,
            "subjects": subjects, "lessons": lessons}


def import_schedule(json_path: str | Path = DEFAULT_JSON,
                    db_path: str | Path | None = None) -> dict[str, int]:
    """Перенести JSON в SQLite одной транзакцией.

    Возвращает число реально добавленных строк по таблицам.
    При любой ошибке SQLite изменения отменяются (rollback).
    """
    rows = build_rows(load_schedule(str(json_path)))
    init_db(db_path)
    statements = (("teachers", INSERT_TEACHER), ("rooms", INSERT_ROOM),
                  ("subjects", INSERT_SUBJECT), ("lessons", INSERT_LESSON))
    added: dict[str, int] = {}
    conn = get_connection(db_path)
    try:
        for table, query in statements:
            cursor = conn.executemany(query, rows[table])
            added[table] = max(cursor.rowcount, 0)
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        print(f"Ошибка импорта, изменения отменены: {exc}")
        raise
    finally:
        conn.close()
    added["lessons_in_json"] = len(rows["lessons"])
    return added


def main(argv: list[str] | None = None) -> int:
    """Точка входа: python -m db.import_json [файл.json]."""
    args = sys.argv[1:] if argv is None else argv
    json_path = Path(args[0]) if args else DEFAULT_JSON
    if not json_path.exists():
        print(f"Файл {json_path} не найден.")
        return 1
    try:
        added = import_schedule(json_path)
    except sqlite3.Error:
        return 1
    print(f"Источник: {json_path}")
    print(f"Добавлено преподавателей: {added['teachers']}")
    print(f"Добавлено аудиторий:      {added['rooms']}")
    print(f"Добавлено предметов:      {added['subjects']}")
    print(f"Добавлено занятий:        {added['lessons']} "
          f"из {added['lessons_in_json']} в JSON")
    skipped = added["lessons_in_json"] - added["lessons"]
    if skipped and added["lessons"] == 0:
        print("Данные уже были импортированы ранее.")
    elif skipped:
        print(f"Пропущено {skipped}: занятие уже есть или совпадает по "
              f"времени с другим в той же аудитории/у того же "
              f"преподавателя.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
