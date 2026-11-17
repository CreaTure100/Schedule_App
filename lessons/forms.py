"""Форма создания и редактирования занятия (ПР11).

LessonForm — ModelForm на основе модели Lesson. Она описывает поля и
проверку данных, а представления (lessons/views.py) только создают
форму, вызывают is_valid() и save().

Правила предметной области проверяются в самой форме:

* длительность занятия — валидатор-функция validate_duration();
* время начала — метод clean_start_time() (учебное время);
* аудитория и преподаватель не должны вести другое проводимое занятие
  в тот же день и время — метод clean() (аналог проверки доступности
  помещения в методичке); отменённые занятия при этом не учитываются.
"""

from datetime import time

from django import forms
from django.core.exceptions import ValidationError

from lessons.models import Lesson

# Учебное время: занятие не может начаться раньше и позже этих границ.
FIRST_START = time(8, 0)
LAST_START = time(21, 0)

# Наибольшая допустимая длительность занятия, часов.
MAX_DURATION_HOURS = 8


def validate_duration(value):
    """Валидатор длительности: больше нуля и не более 8 часов."""
    if value <= 0:
        raise ValidationError("Длительность должна быть больше нуля.")
    if value > MAX_DURATION_HOURS:
        raise ValidationError(
            f"Длительность не может быть больше {MAX_DURATION_HOURS} ч."
        )


class LessonForm(forms.ModelForm):
    """Занятие: предмет, преподаватель, аудитория, день и время.

    Поле status в форму не входит: новое занятие получает статус
    «проводится» по умолчанию модели, а менять статус пользователь может
    только отдельной операцией «Отменить занятие».
    """

    # Поле объявлено явно, чтобы подключить пользовательский валидатор.
    duration_hours = forms.FloatField(
        label="Длительность, ч",
        initial=1.5,
        validators=[validate_duration],
        help_text="Например, 1.5 — полтора часа (не более 8).",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.25",
            "min": "0.25",
        }),
    )

    class Meta:
        model = Lesson
        # Список полей задан явно: пользователь не должен менять
        # служебные значения (status, даты создания и изменения).
        fields = [
            "subject", "teacher", "room", "day", "start_time",
            "duration_hours", "lesson_type",
        ]
        widgets = {
            "subject": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "room": forms.Select(attrs={"class": "form-select"}),
            "day": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"},
                format="%H:%M",
            ),
            "lesson_type": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            "subject": "Предметы добавляются в административной панели.",
            "start_time": "Учебное время: с 08:00 до 21:00.",
            "lesson_type": "Можно оставить пустым — обычное занятие.",
        }

    def clean_start_time(self):
        """Время начала должно быть в пределах учебного дня."""
        start_time = self.cleaned_data["start_time"]
        if not FIRST_START <= start_time <= LAST_START:
            raise ValidationError(
                "Занятие должно начинаться с "
                f"{FIRST_START:%H:%M} до {LAST_START:%H:%M}."
            )
        return start_time

    def clean(self):
        """Проверить доступность аудитории и преподавателя.

        Занятия сравниваются только среди проводимых (active()):
        отменённое занятие не блокирует слот. При редактировании само
        занятие исключается из проверки (exclude(pk=...)), иначе оно
        «конфликтовало» бы с собой.
        """
        cleaned_data = super().clean()
        day = cleaned_data.get("day")
        start_time = cleaned_data.get("start_time")
        room = cleaned_data.get("room")
        teacher = cleaned_data.get("teacher")

        # Проверяем только если все нужные поля прошли базовую проверку.
        if day is None or start_time is None:
            return cleaned_data

        same_slot = Lesson.objects.active().at(day, start_time)
        if self.instance.pk:
            same_slot = same_slot.exclude(pk=self.instance.pk)

        if room and same_slot.filter(room=room).exists():
            self.add_error(
                None, "В это время аудитория занята другим занятием.")
        if teacher and same_slot.filter(teacher=teacher).exists():
            self.add_error(
                None, "В это время преподаватель ведёт другое занятие.")
        return cleaned_data
