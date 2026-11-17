"""Конфигурация приложения «Аудитории»."""

from django.apps import AppConfig


class RoomsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rooms'
    # Название приложения в Django Admin (ПР10).
    verbose_name = "Аудитории"
