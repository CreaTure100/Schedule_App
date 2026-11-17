"""Просмотр структуры исходной базы ПР7 (ПР9, подготовка к переносу).

Скрипт только читает базу data/roomly.sqlite: выводит таблицы, столбцы
и число записей. Запуск из корня проекта:

    python -m db.inspect_source_db
"""

import sqlite3
from contextlib import closing
from pathlib import Path

# Корень проекта: файл лежит в подкаталоге db, на уровень выше — корень.
BASE_DIR = Path(__file__).resolve().parent.parent

# Исходная база, созданная в предыдущих практических работах.
SOURCE_DB = BASE_DIR / "data" / "roomly.sqlite"


def main() -> None:
    """Вывести таблицы, столбцы и количество записей исходной базы."""
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Исходная база не найдена: {SOURCE_DB}")

    with closing(sqlite3.connect(SOURCE_DB)) as connection:
        connection.row_factory = sqlite3.Row

        # Пользовательские таблицы базы данных.
        tables = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()

        for (table_name,) in tables:
            print(f"\nТаблица: {table_name}")

            # Имена, типы, NOT NULL и первичный ключ каждого столбца.
            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
            print("Столбцы:")
            for column in columns:
                print(f" имя={column['name']}, "
                      f"тип={column['type']}, "
                      f"NOT NULL={column['notnull']}, "
                      f"PRIMARY KEY={column['pk']}")

            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]
            print(f"Количество записей: {count}")


if __name__ == "__main__":
    main()
