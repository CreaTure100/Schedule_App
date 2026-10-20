"""Тесты слоя SQLite (ПР7): схема, импорт из JSON, файл запросов."""

import json
import sqlite3

import pytest

from db import check, import_json
from db.check import format_table, load_queries
from db.database import get_connection, init_db, list_tables, unicode_lower
from db.import_json import import_schedule, room_floor, split_subject

DATA = [
    {"day": "Понедельник", "time": "09:00", "subject": "Математика",
     "teacher": "Иванов И.И.", "room": "301"},
    {"day": "Понедельник", "time": "10:45",
     "subject": "Химия (лабораторная)",
     "teacher": "Иванов И.И.", "room": "302"},
    {"day": "Вторник", "time": "9:00", "subject": "Физика",
     "teacher": "Петров П.П.", "room": "301"},
]


def write_json(tmp_path, data=DATA):
    """Записать данные во временный JSON и вернуть путь."""
    path = tmp_path / "schedule.json"
    path.write_text(json.dumps(data, ensure_ascii=False),
                    encoding="utf-8")
    return path


@pytest.fixture
def db_path(tmp_path):
    """База с созданной схемой, но без данных."""
    return init_db(tmp_path / "data" / "test.sqlite")


@pytest.fixture
def loaded_db(tmp_path):
    """База с данными, импортированными из временного JSON."""
    path = tmp_path / "loaded.sqlite"
    import_schedule(write_json(tmp_path), path)
    return path


def count(path, table):
    conn = get_connection(path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


# ---------- схема ----------


def test_init_db_creates_file_and_tables(db_path):
    assert db_path.exists()
    conn = get_connection(db_path)
    try:
        assert list_tables(conn) == ["lessons", "rooms", "subjects",
                                     "teachers"]
    finally:
        conn.close()


def test_init_db_can_run_twice(db_path):
    assert init_db(db_path) == db_path


def test_foreign_keys_are_declared_and_enabled(db_path):
    conn = get_connection(db_path)
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        keys = conn.execute("PRAGMA foreign_key_list(lessons)").fetchall()
        assert {row["table"] for row in keys} == {
            "subjects", "teachers", "rooms"}
    finally:
        conn.close()


def test_foreign_key_violation_is_rejected(db_path):
    conn = get_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO lessons (day, day_number, start_time, "
                "subject_id, teacher_id, room_id) "
                "VALUES ('Понедельник', 1, '09:00', 99, 99, 99)")
    finally:
        conn.close()


def test_check_constraint_rejects_unknown_day(db_path):
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO subjects (title) VALUES ('Физика')")
        conn.execute("INSERT INTO teachers (full_name, surname) "
                     "VALUES ('Иванов И.И.', 'Иванов')")
        conn.execute("INSERT INTO rooms (number) VALUES ('301')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO lessons (day, day_number, start_time, "
                "subject_id, teacher_id, room_id) "
                "VALUES ('Воскресенье', 1, '09:00', 1, 1, 1)")
    finally:
        conn.close()


# ---------- импорт ----------


def test_split_subject():
    assert split_subject("Физика") == ("Физика", None)
    assert split_subject("Химия (лабораторная)") == (
        "Химия", "лабораторная")
    assert split_subject("Химия (Лабораторная) ") == (
        "Химия", "лабораторная")


def test_room_floor():
    assert room_floor("301") == 3
    assert room_floor("12а") is None
    assert room_floor("5") is None


def test_import_fills_all_tables(loaded_db):
    assert count(loaded_db, "teachers") == 2
    assert count(loaded_db, "rooms") == 2
    assert count(loaded_db, "subjects") == 3
    assert count(loaded_db, "lessons") == 3


def test_import_stores_normalized_values(loaded_db):
    conn = get_connection(loaded_db)
    try:
        lab = conn.execute(
            "SELECT l.lesson_type, l.duration_hours, s.title "
            "FROM lessons AS l JOIN subjects AS s ON s.id = l.subject_id "
            "WHERE l.lesson_type IS NOT NULL").fetchone()
        assert (lab["lesson_type"], lab["title"]) == (
            "лабораторная", "Химия")
        assert lab["duration_hours"] == 1.5  # DEFAULT из schema.sql
        time = conn.execute(
            "SELECT start_time, day_number FROM lessons "
            "WHERE day = 'Вторник'").fetchone()
        assert (time["start_time"], time["day_number"]) == ("09:00", 2)
        floor = conn.execute(
            "SELECT floor FROM rooms WHERE number = '301'").fetchone()
        assert floor["floor"] == 3
    finally:
        conn.close()


def test_import_twice_does_not_duplicate(tmp_path, loaded_db):
    added = import_schedule(tmp_path / "schedule.json", loaded_db)
    assert added["lessons"] == 0
    assert count(loaded_db, "lessons") == 3
    assert count(loaded_db, "teachers") == 2


def test_import_skips_double_booked_room(tmp_path):
    data = [
        {"day": "Среда", "time": "09:00", "subject": "Физика",
         "teacher": "Иванов И.И.", "room": "301"},
        {"day": "Среда", "time": "09:00", "subject": "Химия",
         "teacher": "Петров П.П.", "room": "301"},
    ]
    path = tmp_path / "conflict.sqlite"
    added = import_schedule(write_json(tmp_path, data), path)
    assert added["lessons_in_json"] == 2
    assert added["lessons"] == 1
    assert count(path, "lessons") == 1


def test_import_rolls_back_on_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(import_json, "INSERT_LESSON",
                        "INSERT INTO no_such_table VALUES (?)")
    path = tmp_path / "failed.sqlite"
    with pytest.raises(sqlite3.Error):
        import_schedule(write_json(tmp_path), path)
    assert "изменения отменены" in capsys.readouterr().out
    # справочники, вставленные до ошибки, тоже откатились
    assert count(path, "teachers") == 0
    assert count(path, "subjects") == 0


def test_main_reports_missing_file(tmp_path, capsys):
    assert import_json.main([str(tmp_path / "нет.json")]) == 1
    assert "не найден" in capsys.readouterr().out


def test_unicode_lower_makes_like_case_insensitive(loaded_db):
    conn = get_connection(loaded_db)
    try:
        query = "SELECT COUNT(*) FROM subjects WHERE lower(title) LIKE ?"
        assert conn.execute(query, ["физ%"]).fetchone()[0] == 0
        conn.create_function("lower", 1, unicode_lower)
        assert conn.execute(query, ["физ%"]).fetchone()[0] == 1
    finally:
        conn.close()
    assert unicode_lower(None) is None


# ---------- файл sql/queries.sql ----------


def test_queries_file_has_enough_queries_of_each_kind():
    queries = load_queries()
    assert len(queries) >= 10
    tags = [tag for query in queries for tag in query["tags"]]
    for kind in ("ORDER", "WHERE", "JOIN", "AGGREGATE", "GROUP"):
        assert tags.count(kind) >= 2, kind


def test_all_queries_run_and_use_known_tables(loaded_db):
    conn = get_connection(loaded_db)
    try:
        for query in load_queries():
            assert "SELECT" in query["sql"], query["number"]
            conn.execute(query["sql"]).fetchall()
    finally:
        conn.close()


def test_queries_give_expected_results_on_test_data(loaded_db):
    queries = {q["number"]: q["sql"] for q in load_queries()}
    conn = get_connection(loaded_db)
    try:
        by_teacher = conn.execute(queries[16]).fetchall()
        assert tuple(by_teacher[0]) == ("Иванов И.И.", 2, 3.0)
        summary = conn.execute(queries[13]).fetchone()
        assert (summary["lessons_count"], summary["first_start"]) == (
            3, "09:00")
        typed = conn.execute(queries[8]).fetchall()
        assert len(typed) == 1
    finally:
        conn.close()


def test_format_table():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT 1 AS a, 'текст' AS b").fetchall()
    text = format_table(rows)
    assert text.splitlines()[0].split() == ["a", "b"]
    assert "текст" in text
    assert format_table([]) == "(пусто)"


def test_check_main_on_loaded_db(loaded_db, monkeypatch, capsys):
    monkeypatch.setattr(check, "get_connection",
                        lambda: get_connection(loaded_db))
    assert check.main(["--queries"]) == 0
    out = capsys.readouterr().out
    assert "foreign_key_list" in out
    assert "Запрос 12" in out
