"""Регистрация моделей приложения «Преподаватели» в админке (ПР10)."""

from django.contrib import admin
from django.db.models import Count

from lessons.models import Lesson
from teachers.models import Teacher


class TeacherLessonInline(admin.TabularInline):
    """Занятия преподавателя прямо в его карточке (встроенная таблица)."""

    model = Lesson
    extra = 0
    fields = (
        "day", "start_time", "subject", "room", "lesson_type", "status",
    )
    autocomplete_fields = ("subject", "room")
    show_change_link = True
    verbose_name = "Занятие преподавателя"
    verbose_name_plural = "Занятия преподавателя"


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Преподаватели: поиск по имени и почте, число занятий."""

    list_display = ("full_name", "surname", "email", "lessons_count")
    list_display_links = ("full_name",)
    search_fields = ("full_name", "surname", "email")
    ordering = ("surname", "full_name")
    list_per_page = 20
    readonly_fields = ("created_at", "updated_at")
    inlines = (TeacherLessonInline,)

    def get_queryset(self, request):
        """Число занятий считает база данных (одним запросом на список)."""
        return super().get_queryset(request).annotate(
            _lessons_count=Count("lessons"))

    @admin.display(description="Занятий", ordering="_lessons_count")
    def lessons_count(self, obj):
        """Число занятий преподавателя (по обратной связи lessons)."""
        return obj._lessons_count
