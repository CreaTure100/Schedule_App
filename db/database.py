"""Подключение к SQLite и создание схемы базы данных (ПР7).

Модуль не зависит от Django: его используют и скрипты (импорт,
проверка), и настройки проекта (путь к файлу базы).

Создать файл базы и таблицы:  python -m db.database
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "roomly.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Открыть соединение с базой.

    Строки результата доступны по имени столбца (sqlite3.Row), а
    проверка внешних ключей включена: в SQLite она по умолчанию
    выключена и включается отдельно для каждого соединения.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def unicode_lower(value: object) -> object:
    """Перевести строку в нижний регистр для SQL-функции lower().

    Встроенные lower() и LIKE в SQLite не различают регистр только у
    латиницы: «физика» не найдёт «Физика». Функция подключается к
    соединению так: conn.create_function("lower", 1, unicode_lower).
    """
    return value.lower() if isinstance(value, str) else value


def init_db(db_path: str | Path | None = None) -> Path:
    """Создать файл базы и таблицы по sql/schema.sql (повторно безопасно)."""
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection(path)
    try:
        conn.executescript(script)
    finally:
        conn.close()
    return path


def list_tables(conn: sqlite3.Connection) -> list[str]:
    """Имена таблиц базы (без служебных таблиц SQLite)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [row["name"] for row in rows]


def main() -> None:
    """Создать базу и показать список таблиц."""
    path = init_db()
    conn = get_connection(path)
    try:
        print(f"База данных: {path}")
        print("Таблицы:", ", ".join(list_tables(conn)))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
