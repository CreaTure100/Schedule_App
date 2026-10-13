"""Сохранение и загрузка данных расписания в JSON.

Формат файла совпадает с ПР2: список словарей с ключами
day, time, subject, teacher, room (teacher и room — строки).
"""

import json
import os

from models import Schedule

DATA_DIR = "data"
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")


def load_schedule(filename: str = SCHEDULE_FILE) -> Schedule:
    """Загрузить расписание из JSON: JSON → dict → объекты Lesson."""
    if not os.path.exists(filename):
        return Schedule()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (ValueError, OSError) as exc:
        # ValueError покрывает JSONDecodeError и UnicodeDecodeError
        print(f"Не удалось прочитать файл {filename}: {exc}")
        return Schedule()
    if not isinstance(raw, list):
        print(f"Не удалось прочитать файл {filename}: "
              f"ожидался список занятий.")
        return Schedule()

    schedule = Schedule()
    for number, item in enumerate(raw, 1):
        try:
            schedule.add_from_dict(item)
        except (KeyError, TypeError, ValueError) as exc:
            print(f"Запись №{number} пропущена "
                  f"({type(exc).__name__}: {exc}).")
    return schedule


def save_schedule(schedule: Schedule,
                  filename: str = SCHEDULE_FILE) -> None:
    """Сохранить расписание в JSON: объекты Lesson → dict → JSON."""
    directory = os.path.dirname(filename)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(schedule.to_dicts(), f, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"Не удалось сохранить файл {filename}: {exc}")
