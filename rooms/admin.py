"""Регистрация моделей приложения «Аудитории» в админке (ПР10)."""

from django.contrib import admin
from django.db.models import Count

from lessons.models import Lesson
from rooms.models import Room


class RoomLessonInline(admin.TabularInline):
    """Занятия аудитории прямо в её карточке (встроенная таблица)."""

    model = Lesson
    extra = 0
    fields = (
        "day", "start_time", "subject", "teacher", "lesson_type", "status",
    )
    autocomplete_fields = ("subject", "teacher")
    # Ссылка «Изменить» ведёт в полную карточку занятия.
    show_change_link = True
    verbose_name = "Занятие в аудитории"
    verbose_name_plural = "Занятия в аудитории"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Аудитории: номер, этаж, вместимость и число занятий."""

    list_display = (
        "number", "floor", "capacity", "is_large", "lessons_count", "slug",
    )
    list_display_links = ("number",)
    # Вместимость можно править прямо в списке (кнопка «Сохранить»).
    list_editable = ("capacity",)
    list_filter = ("floor", "is_large")
    search_fields = ("number",)
    ordering = ("number",)
    list_per_page = 20
    # is_large вычисляет база данных, slug создаётся автоматически.
    readonly_fields = ("is_large", "slug", "created_at", "updated_at")
    # image (ПР11): изображение загружается прямо в карточке аудитории.
    fields = (
        "number", "floor", "capacity", "image", "is_large", "slug",
        "created_at", "updated_at",
    )
    inlines = (RoomLessonInline,)

    def get_queryset(self, request):
        """Число занятий считает база данных (одним запросом на список)."""
        return super().get_queryset(request).annotate(
            _lessons_count=Count("lessons"))

    @admin.display(description="Занятий", ordering="_lessons_count")
    def lessons_count(self, obj):
        """Число занятий аудитории (по обратной связи lessons)."""
        return obj._lessons_count
