"""Конфигурация приложения «База данных» (страницы на SQLite)."""

from django.apps import AppConfig


class DbpagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dbpages'
