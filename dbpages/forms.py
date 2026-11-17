"""Формы раздела «Статистика и поиск» (ПР11).

LessonFilterForm — обычная форма (forms.Form): она не создаёт объектов,
а только получает и проверяет GET-параметры фильтрации списка занятий.
Имена полей совпадают с прежними GET-параметрами (day, teacher, room,
q, sort), поэтому адреса и ссылки пагинации не изменились. Номер
страницы (page) к условиям фильтрации не относится и в форму не входит.
"""

from django import forms
from django.core.exceptions import ValidationError

from models import DAYS
from rooms.models import Room
from teachers.models import Teacher

# Допустимые варианты сортировки (значения совпадают с ключами словаря
# SORT_FIELDS в dbpages/views.py: имя поля ORM в запрос не попадает).
SORT_CHOICES = [
    ("day", "Дню и времени"),
    ("subject", "Предмету"),
    ("teacher", "Преподавателю"),
    ("room", "Аудитории"),
]


class SafeModelChoiceField(forms.ModelChoiceField):
    """Выбор объекта по идентификатору без «мусора» в запросе к базе.

    Как и parse_id() в ПР9, принимает только короткую запись из
    ASCII-цифр. Всё остальное («abc», «-1», «²», слишком длинное число)
    сразу становится ошибкой поля и до базы данных не доходит.
    """

    def to_python(self, value):
        """Проверить запись идентификатора и найти объект."""
        if value in self.empty_values:
            return None
        text = str(value).strip()
        if not (text.isascii() and text.isdigit() and len(text) <= 9):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )
        return super().to_python(text)


class LessonFilterForm(forms.Form):
    """Фильтры списка занятий: день, преподаватель, аудитория, предмет."""

    day = forms.ChoiceField(
        required=False,
        label="День недели",
        choices=[("", "Любой")] + [(name, name) for name in DAYS],
        error_messages={"invalid_choice": "Выберите день недели из списка."},
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    teacher = SafeModelChoiceField(
        queryset=Teacher.objects.order_by("surname", "full_name"),
        required=False,
        label="Преподаватель",
        empty_label="Все преподаватели",
        error_messages={"invalid_choice": "Выберите преподавателя из списка."},
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    room = SafeModelChoiceField(
        queryset=Room.objects.order_by("number"),
        required=False,
        label="Аудитория",
        empty_label="Все аудитории",
        error_messages={"invalid_choice": "Выберите аудиторию из списка."},
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(
        required=False,
        max_length=200,
        label="Предмет",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "type": "search",
            "placeholder": "Например, физика",
        }),
    )
    sort = forms.ChoiceField(
        required=False,
        label="Сортировать по",
        choices=SORT_CHOICES,
        error_messages={"invalid_choice": "Выберите вариант сортировки."},
        widget=forms.Select(attrs={"class": "form-select"}),
    )
