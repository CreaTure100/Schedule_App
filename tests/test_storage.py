"""Тесты загрузки и сохранения JSON."""

import json

from models import Schedule
from storage import load_schedule, save_schedule

PR2_DATA = [
    {"day": "Понедельник", "time": "09:00", "subject": "Математика",
     "teacher": "Иванов И.И.", "room": "301"},
    {"day": "Вторник", "time": "10:00", "subject": "Физика",
     "teacher": "Иванов И.И.", "room": "301"},
]


def test_load_missing_file_returns_empty(tmp_path):
    schedule = load_schedule(str(tmp_path / "нет.json"))
    assert isinstance(schedule, Schedule)
    assert len(schedule) == 0


def test_load_pr2_format(tmp_path):
    path = tmp_path / "schedule.json"
    path.write_text(json.dumps(PR2_DATA, ensure_ascii=False),
                    encoding="utf-8")
    schedule = load_schedule(str(path))
    assert len(schedule) == 2
    assert schedule[0].teacher.name == "Иванов И.И."
    assert schedule[0].room.number == "301"


def test_load_restores_shared_references(tmp_path):
    path = tmp_path / "schedule.json"
    path.write_text(json.dumps(PR2_DATA), encoding="utf-8")
    schedule = load_schedule(str(path))
    assert schedule[0].teacher is schedule[1].teacher
    assert schedule[0].room is schedule[1].room


def test_save_and_load_roundtrip(tmp_path, sample_schedule):
    path = str(tmp_path / "data" / "schedule.json")
    save_schedule(sample_schedule, path)
    restored = load_schedule(path)
    assert restored.lessons == sample_schedule.lessons


def test_saved_json_uses_pr2_format(tmp_path, sample_schedule):
    path = tmp_path / "schedule.json"
    save_schedule(sample_schedule, str(path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw[0] == {
        "day": "Понедельник", "time": "14:00", "subject": "Математика",
        "teacher": "Иванов И.И.", "room": "301",
    }
    assert "Математика" in path.read_text(encoding="utf-8")


def test_save_to_file_without_directory(tmp_path, monkeypatch,
                                        sample_schedule):
    monkeypatch.chdir(tmp_path)
    save_schedule(sample_schedule, "schedule.json")
    assert (tmp_path / "schedule.json").exists()


def test_load_broken_json(tmp_path, capsys):
    path = tmp_path / "schedule.json"
    path.write_text("{не json", encoding="utf-8")
    assert len(load_schedule(str(path))) == 0
    assert "Не удалось прочитать файл" in capsys.readouterr().out


def test_load_not_a_list(tmp_path, capsys):
    path = tmp_path / "schedule.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert len(load_schedule(str(path))) == 0
    assert "ожидался список" in capsys.readouterr().out


def test_load_skips_invalid_records(tmp_path, capsys):
    data = PR2_DATA + [
        {"day": "Среда", "time": "99:99", "subject": "X",
         "teacher": "Т", "room": "1"},
        {"day": "Среда"},
        "мусор",
    ]
    path = tmp_path / "schedule.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    schedule = load_schedule(str(path))
    assert len(schedule) == 2
    assert capsys.readouterr().out.count("пропущена") == 3
