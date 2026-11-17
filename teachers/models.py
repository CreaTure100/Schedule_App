"""Модель Django ORM «Преподаватель» (ПР9).

Соответствует таблице teachers из ПР7 (sql/schema.sql). Не путать с
классом models.Teacher из пакета models/ в корне проекта (ПР3): тот —
обычный класс Python без базы данных.
"""

from django.db import models

from homepage.models import TimeStampedModel


class Teacher(TimeStampedModel):
    """Преподаватель, ведущий занятия."""

    # Имя в формате «Иванов И.И.»; уникально, как в таблице ПР7.
    full_name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="ФИО",
    )

    # Фамилия нужна для сортировки и поиска. Если не указана,
    # заполняется в save() первым словом из full_name.
    surname = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Фамилия",
    )

    # Необязательное поле: blank=True разрешает пустое значение в
    # формах, default="" хранит «нет адреса» пустой строкой, а не NULL.
    email = models.EmailField(
        blank=True,
        default="",
        verbose_name="Электронная почта",
    )

    def save(self, *args, **kwargs):
        """Сохранить преподавателя, заполнив фамилию при её отсутствии."""
        if not self.surname and self.full_name.strip():
            self.surname = self.full_name.split()[0]
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = {*update_fields, "surname"}
        super().save(*args, **kwargs)

    def __str__(self):
        """Текстовое представление: имя преподавателя."""
        return self.full_name

    class Meta:
        # Сортировка по умолчанию: фамилия, затем полное имя.
        ordering = ["surname", "full_name"]
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
