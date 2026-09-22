"""Сохранение и загрузка данных расписания в JSON."""

import json
import os
from typing import Any

DATA_DIR = "data"
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")


def load_schedule(filename: str = SCHEDULE_FILE) -> list[dict[str, Any]]:
    """Загрузить список занятий из JSON-файла."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Не удалось прочитать файл {filename}: {exc}")
        return []


def save_schedule(schedule: list[dict[str, Any]],
                  filename: str = SCHEDULE_FILE) -> None:
    """Сохранить список занятий в JSON-файл."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"Не удалось сохранить файл {filename}: {exc}")
