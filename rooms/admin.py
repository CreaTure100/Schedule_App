"""Регистрация моделей приложения «Аудитории» в админке."""

from django.contrib import admin

from rooms.models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Аудитории: номер, этаж и вместимость."""

    list_display = ("number", "floor", "capacity")
    search_fields = ("number",)
