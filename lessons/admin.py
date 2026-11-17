"""Регистрация моделей приложения «Занятия» в админке (ПР10).

Админка не заменяет правила предметной области: уникальность
«аудитория + день + время» и «преподаватель + день + время» среди
проводимых занятий проверяют ограничения модели Lesson (их выполняют
формы админки при сохранении). С ПР11 у занятия есть статус: отменённые
занятия остаются в админке, но не блокируют аудиторию и преподавателя.
"""

from django.contrib import admin
from django.db.models import Count

from lessons.models import Lesson, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Предметы: список с поиском по названию и числом занятий."""

    list_display = ("title", "lessons_count")
    search_fields = ("title",)
    ordering = ("title",)
    list_per_page = 20
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        """Число занятий считает база данных (одним запросом на список)."""
        return super().get_queryset(request).annotate(
            _lessons_count=Count("lessons"))

    @admin.display(description="Занятий", ordering="_lessons_count")
    def lessons_count(self, obj):
        """Число занятий по предмету."""
        return obj._lessons_count


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Занятия: фильтры, поиск по связанным моделям и массовые действия."""

    list_display = (
        "subject", "day", "start_time", "teacher", "room", "lesson_type",
        "status",
    )
    list_display_links = ("subject",)
    list_filter = ("status", "day", "lesson_type", "room", "teacher")
    # Поиск по полям связанных моделей через двойное подчёркивание.
    search_fields = (
        "subject__title", "teacher__full_name", "teacher__surname",
        "room__number",
    )
    ordering = ("day", "start_time")
    list_per_page = 20
    # JOIN вместо отдельного запроса на каждую строку списка.
    list_select_related = ("subject", "teacher", "room")
    autocomplete_fields = ("subject", "teacher", "room")
    readonly_fields = ("created_at", "updated_at")
    actions = ("mark_laboratory", "clear_lesson_type", "cancel_lessons")

    @admin.action(description="Отметить выбранные занятия как лабораторные")
    def mark_laboratory(self, request, queryset):
        """Массово установить тип «лабораторная» (один UPDATE)."""
        updated = queryset.update(lesson_type=Lesson.LessonType.LABORATORY)
        self.message_user(request, f"Изменено занятий: {updated}.")

    @admin.action(description="Отменить выбранные занятия")
    def cancel_lessons(self, request, queryset):
        """Массово отменить занятия (ПР11): статус, а не удаление."""
        updated = queryset.update(status=Lesson.Status.CANCELLED)
        self.message_user(request, f"Отменено занятий: {updated}.")

    @admin.action(description="Сбросить тип у выбранных занятий")
    def clear_lesson_type(self, request, queryset):
        """Массово сделать занятия обычными (пустой тип)."""
        updated = queryset.update(lesson_type="")
        self.message_user(request, f"Изменено занятий: {updated}.")
