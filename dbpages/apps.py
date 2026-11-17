"""Конфигурация приложения «База данных» (страницы на Django ORM)."""

from django.apps import AppConfig


class DbpagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dbpages'
    # Название приложения в Django Admin (ПР10).
    verbose_name = "Статистика и поиск"
