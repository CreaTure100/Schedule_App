"""Страницы приложения «Занятия»: данные берутся через Django ORM.

С ПР11 здесь также создание, редактирование и отмена занятий. Формы
(LessonForm) описаны в lessons/forms.py, а представления только создают
форму, вызывают is_valid() и сохраняют объект.
"""

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from lessons import presenters
from lessons.forms import LessonForm
from lessons.models import Lesson
from schedule import get_day_status

# Ошибка гонки: два одновременных запроса прошли проверку формы, и
# второй сохранить занятие не смог (сработало ограничение базы данных).
SLOT_BUSY_MESSAGE = (
    "Не удалось сохранить занятие: аудитория или преподаватель "
    "уже заняты в это время."
)


def lesson_list(request: HttpRequest) -> HttpResponse:
    """Список проводимых занятий, сгруппированных по дням недели."""
    # select_related() подтягивает предмет, преподавателя и аудиторию
    # тем же запросом (JOIN), а order_by() сортирует по дню и времени:
    # вся страница строится одним обращением к базе данных. active()
    # исключает отменённые занятия (ПР11).
    lessons = list(
        Lesson.objects
        .active()
        .with_related()
        .order_by("day", "start_time", "pk")
    )
    context = {
        "lessons": presenters.build_lesson_items(lessons),
        "days": presenters.build_day_groups(lessons),
    }
    return render(request, "lessons/lesson_list.html", context)


def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """Страница одного занятия (lesson_id — первичный ключ записи)."""
    # Если записи нет, get_object_or_404() вызывает Http404, и Django
    # показывает страницу 404 (handler404) без необработанного исключения.
    # Отменённое занятие в расписании не показывается: для него тоже 404.
    lesson = get_object_or_404(
        Lesson.objects.active().select_related("subject", "teacher", "room"),
        pk=lesson_id,
    )
    context = {
        "lesson": presenters.build_lesson_item(lesson),
        "day_status": get_day_status(
            lesson.get_day_display(), timezone.localdate()),
    }
    return render(request, "lessons/lesson_detail.html", context)


def initial_from_query(request: HttpRequest) -> dict[str, str]:
    """Начальные значения формы из GET-параметров room и teacher.

    Нужны для ссылки «Добавить занятие» на страницах аудитории и
    преподавателя. Это только предзаполнение списка: настоящая проверка
    значения выполняется формой при отправке (POST).
    """
    initial = {}
    for name in ("room", "teacher"):
        value = request.GET.get(name, "")
        if value.isascii() and value.isdigit():
            initial[name] = value
    return initial


def lesson_create(request: HttpRequest) -> HttpResponse:
    """Добавление занятия: GET — пустая форма, POST — сохранение."""
    if request.method == "POST":
        form = LessonForm(request.POST)
        # Данные сохраняются только после успешной проверки формы.
        if form.is_valid():
            try:
                # atomic() нужен, чтобы ошибка базы данных не оставила
                # открытую транзакцию.
                with transaction.atomic():
                    lesson = form.save()
            except IntegrityError:
                form.add_error(None, SLOT_BUSY_MESSAGE)
            else:
                messages.success(request, "Занятие добавлено в расписание.")
                return redirect("lessons:detail", lesson_id=lesson.pk)
    else:
        form = LessonForm(initial=initial_from_query(request))
    return render(request, "lessons/lesson_form.html", {"form": form})


def lesson_update(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """Редактирование занятия через ту же форму (instance=lesson)."""
    # Редактировать можно только проводимое занятие: отменённое по
    # прямому адресу не открывается (404).
    lesson = get_object_or_404(Lesson.objects.active(), pk=lesson_id)
    if request.method == "POST":
        # instance связывает форму с существующей записью: save()
        # обновит её, а не создаст новую.
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            try:
                with transaction.atomic():
                    lesson = form.save()
            except IntegrityError:
                form.add_error(None, SLOT_BUSY_MESSAGE)
            else:
                messages.success(request, "Изменения сохранены.")
                return redirect("lessons:detail", lesson_id=lesson.pk)
    else:
        form = LessonForm(instance=lesson)
    context = {"form": form, "lesson_id": lesson_id}
    return render(request, "lessons/lesson_form.html", context)


@require_POST
def lesson_cancel(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """Отмена занятия: статус меняется на «отменено», запись остаётся.

    Операция меняет данные, поэтому разрешён только POST (GET даёт 405),
    а форма отмены в шаблоне содержит CSRF-токен.
    """
    lesson = get_object_or_404(Lesson.objects.active(), pk=lesson_id)
    lesson.cancel()
    messages.success(
        request, "Занятие отменено. Запись сохранена в базе данных.")
    return redirect("lessons:list")
