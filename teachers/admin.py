"""Регистрация моделей приложения «Преподаватели» в админке."""

from django.contrib import admin

from teachers.models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Преподаватели: список с поиском по имени."""

    list_display = ("full_name", "surname", "email")
    search_fields = ("full_name", "email")
