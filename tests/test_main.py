"""Сквозной тест меню: добавление, поиск и удаление занятия."""

import json

import main


def run_menu(monkeypatch, answers):
    """Запустить main() с заранее заданными ответами пользователя."""
    iterator = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(iterator))
    main.main()


def test_add_find_delete_flow(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run_menu(monkeypatch, [
        "2", "1", "9:00", "Математика", "Иванов И.И.", "301",  # добавить
        "4", "матем",                                           # найти
        "3", "1",                                               # удалить
        "0",
    ])
    out = capsys.readouterr().out
    assert "Занятие добавлено." in out
    assert "1. Понедельник | 09:00 | Математика | Иванов И.И. | ауд. 301" \
        in out
    assert "Удалено: Математика" in out
    saved = json.loads((tmp_path / "data" / "schedule.json")
                       .read_text(encoding="utf-8"))
    assert saved == []


def test_invalid_time_shows_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run_menu(monkeypatch, [
        "2", "1", "25:00", "Математика", "Иванов И.И.", "301", "0",
    ])
    out = capsys.readouterr().out
    assert "Ошибка: Неверное время" in out
    assert not (tmp_path / "data" / "schedule.json").exists()


def test_unknown_command(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run_menu(monkeypatch, ["99", "0"])
    assert "Неизвестная команда." in capsys.readouterr().out
