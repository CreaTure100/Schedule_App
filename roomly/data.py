"""Источник данных для страниц сайта: база SQLite (ПР7)."""

from django.conf import settings

from db.repository import load_schedule_from_db
from models import Schedule


def get_schedule() -> Schedule:
    """Расписание из базы данных (путь — settings.SQLITE_PATH)."""
    return load_schedule_from_db(settings.SQLITE_PATH)
