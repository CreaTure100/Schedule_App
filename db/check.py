"""Проверка базы данных: структура, данные, SQL-запросы (ПР7).

    python -m db.check            структура, количество строк, JOIN
    python -m db.check --queries  то же + все запросы из sql/queries.sql
"""

import re
import sqlite3
import sys
from pathlib import Path

from db.database import BASE_DIR, get_connection, list_tables

QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"
HEADER_RE = re.compile(
    r"^-- Запрос (?P<number>\d+) \[(?P<tags>[^\]]+)\]\. (?P<title>.*)$"
)
CHECK_JOIN = (
    "SELECT l.day, l.start_time, s.title AS subject, "
    "t.full_name AS teacher, r.number AS room "
    "FROM lessons AS l "
    "JOIN subjects AS s ON s.id = l.subject_id "
    "JOIN teachers AS t ON t.id = l.teacher_id "
    "JOIN rooms AS r ON r.id = l.room_id "
    "ORDER BY l.day_number, l.start_time LIMIT 5"
)


def load_queries(path: Path = QUERIES_PATH) -> list[dict]:
    """Разобрать queries.sql: номер, теги, название и текст запроса."""
    queries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        header = HEADER_RE.match(line)
        if header:
            queries.append({
                "number": int(header["number"]),
                "tags": [tag.strip() for tag in header["tags"].split(",")],
                "title": header["title"],
                "sql": "",
            })
        elif queries and not line.startswith("-- ----------"):
            queries[-1]["sql"] += line + "\n"
    for query in queries:
        query["sql"] = query["sql"].strip()
    return queries


def format_table(rows: list[sqlite3.Row]) -> str:
    """Строки результата в виде выровненной текстовой таблицы."""
    if not rows:
        return "(пусто)"
    columns = rows[0].keys()
    cells = [[str(row[name]) for name in columns] for row in rows]
    widths = [max(len(name), *(len(line[i]) for line in cells))
              for i, name in enumerate(columns)]
    lines = ["  ".join(name.ljust(widths[i])
                       for i, name in enumerate(columns))]
    lines.append("  ".join("-" * width for width in widths))
    lines.extend("  ".join(value.ljust(widths[i])
                           for i, value in enumerate(line))
                 for line in cells)
    return "\n".join(lines)


def show_structure(conn: sqlite3.Connection) -> None:
    """Таблицы и внешние ключи таблицы lessons."""
    print("== Таблицы ==")
    print(format_table(conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()))
    print("\n== PRAGMA foreign_key_list(lessons) ==")
    print(format_table(conn.execute(
        "PRAGMA foreign_key_list(lessons)").fetchall()))
    print("\n== PRAGMA foreign_key_check (пусто — нарушений нет) ==")
    print(format_table(conn.execute(
        "PRAGMA foreign_key_check").fetchall()))


def show_counts(conn: sqlite3.Connection) -> None:
    """Количество записей в каждой таблице."""
    print("\n== Количество записей ==")
    for table in list_tables(conn):
        # Имена таблиц берутся из sqlite_master, а не от пользователя.
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:10s} {count}")


def run_queries(conn: sqlite3.Connection) -> None:
    """Выполнить все запросы из sql/queries.sql и показать результат."""
    for query in load_queries():
        tags = ", ".join(query["tags"])
        print(f"\n== Запрос {query['number']} [{tags}]. {query['title']}")
        print(format_table(conn.execute(query["sql"]).fetchall()))


def main(argv: list[str] | None = None) -> int:
    """Точка входа проверки."""
    args = sys.argv[1:] if argv is None else argv
    conn = get_connection()
    try:
        show_structure(conn)
        show_counts(conn)
        print("\n== JOIN: первые 5 занятий с названиями ==")
        print(format_table(conn.execute(CHECK_JOIN).fetchall()))
        if "--queries" in args:
            run_queries(conn)
    except sqlite3.Error as exc:
        print(f"Ошибка: {exc}. Сначала выполните: python -m db.import_json")
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
