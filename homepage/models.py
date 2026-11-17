"""Общие абстрактные модели проекта (ПР9).

Абстрактная модель не создаёт собственной таблицы: её поля копируются
в таблицы моделей-наследников (Teacher, Room, Subject, Lesson).
"""

from django.db import models


class TimeStampedModel(models.Model):
    """Время создания и последнего изменения записи."""

    # auto_now_add: значение ставится один раз, при создании записи.
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )

    # auto_now: значение обновляется при каждом save().
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Изменено",
    )

    class Meta:
        abstract = True
