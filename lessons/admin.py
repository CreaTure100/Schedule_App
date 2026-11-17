"""Регистрация моделей приложения «Занятия» в админке."""

from django.contrib import admin

from lessons.models import Lesson, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Предметы: список с поиском по названию."""

    search_fields = ("title",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Занятия: фильтр по дню и поиск по предмету и преподавателю."""

    list_display = ("subject", "day", "start_time", "teacher", "room")
    list_filter = ("day",)
    list_select_related = ("subject", "teacher", "room")
    search_fields = ("subject__title", "teacher__full_name")
