"""Перенос данных из исходной базы ПР7 в базу Django (ПР9).

Исходная база data/roomly.sqlite только читается (модулем sqlite3), а
записи создаются через ORM в базе, настроенной в DATABASES (db.sqlite3).
Первичные ключи сохраняются, поэтому связи между записями не теряются.

Порядок запуска из корня проекта:

    python manage.py migrate
    python -m db.import_sqlite_to_orm

Повторный запуск безопасен: update_or_create() обновляет записи с
теми же ключами и не создаёт дубликатов.
"""

import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "roomly.sqlite"

# Формат времени в исходной базе (CHECK start_time GLOB ... в схеме ПР7).
SOURCE_TIME_FORMAT = "%H:%M"


def parse_time(value: str) -> time:
    """Строка «ЧЧ:ММ» из исходной базы → объект time для TimeField."""
    return datetime.strptime(value.strip(), SOURCE_TIME_FORMAT).time()


def read_source(source_db: str | Path) -> dict[str, list[sqlite3.Row]]:
    """Прочитать все таблицы исходной базы (только запросы SELECT)."""
    queries = {
        "teachers": "SELECT id, full_name, surname, email "
                    "FROM teachers ORDER BY id",
        "rooms": "SELECT id, number, floor, capacity "
                 "FROM rooms ORDER BY id",
        "subjects": "SELECT id, title FROM subjects ORDER BY id",
        "lessons": "SELECT id, day_number, start_time, duration_hours, "
                   "lesson_type, subject_id, teacher_id, room_id "
                   "FROM lessons ORDER BY id",
    }
    with closing(sqlite3.connect(source_db)) as connection:
        connection.row_factory = sqlite3.Row
        return {name: connection.execute(query).fetchall()
                for name, query in queries.items()}


def import_data(source_db: str | Path = SOURCE_DB) -> dict[str, int]:
    """Перенести данные из source_db в базу Django.

    Возвращает число записей каждой таблицы в базе Django после переноса.
    Всё выполняется одной транзакцией: при ошибке изменения откатываются.
    """
    # Модели импортируются здесь: Django должен быть уже настроен.
    from django.db import transaction

    from lessons.models import Lesson, Subject
    from rooms.models import Room
    from teachers.models import Teacher

    source = read_source(source_db)

    with transaction.atomic():
        # Сначала независимые сущности, затем занятия, которые на них
        # ссылаются внешними ключами.
        for row in source["teachers"]:
            Teacher.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "full_name": row["full_name"],
                    "surname": row["surname"],
                    # В исходной базе email может быть NULL.
                    "email": row["email"] or "",
                },
            )
        for row in source["rooms"]:
            Room.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "number": row["number"],
                    "floor": row["floor"],
                    "capacity": row["capacity"],
                },
            )
        for row in source["subjects"]:
            Subject.objects.update_or_create(
                pk=row["id"],
                defaults={"title": row["title"]},
            )
        for row in source["lessons"]:
            Lesson.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "day": row["day_number"],
                    "start_time": parse_time(row["start_time"]),
                    "duration_hours": row["duration_hours"],
                    # NULL («обычное занятие») → пустая строка.
                    "lesson_type": row["lesson_type"] or "",
                    "subject_id": row["subject_id"],
                    "teacher_id": row["teacher_id"],
                    "room_id": row["room_id"],
                },
            )

    return {
        "teachers": Teacher.objects.count(),
        "rooms": Room.objects.count(),
        "subjects": Subject.objects.count(),
        "lessons": Lesson.objects.count(),
    }


def setup_django() -> None:
    """Настроить Django, если скрипт запущен как отдельная программа."""
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roomly.settings")
    import django
    django.setup()


def main() -> int:
    """Точка входа: перенос и сверка количества записей."""
    if not SOURCE_DB.exists():
        print(f"Исходная база не найдена: {SOURCE_DB}")
        return 1
    setup_django()
    source = read_source(SOURCE_DB)
    imported = import_data(SOURCE_DB)

    print("Перенос данных завершён.")
    ok = True
    for name, rows in source.items():
        print(f"{name}: в исходной базе {len(rows)}, "
              f"в базе Django {imported[name]}")
        ok = ok and len(rows) <= imported[name]
    if not ok:
        print("Количество записей не совпало: проверьте перенос.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
