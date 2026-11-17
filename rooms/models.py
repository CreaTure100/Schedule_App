"""Модель Django ORM «Аудитория» (ПР9).

Соответствует таблице rooms из ПР7 (sql/schema.sql). Не путать с
классом models.Room из пакета models/ в корне проекта (ПР3).
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from homepage.models import TimeStampedModel


class Room(TimeStampedModel):
    """Аудитория, в которой проходят занятия."""

    # Номер — строка («301», «12а»), поэтому CharField, а не число.
    number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номер аудитории",
    )

    # null=True: в базе допускается NULL (этаж неизвестен, если номер
    # нечисловой); blank=True: поле необязательно в формах.
    floor = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Этаж",
    )

    # Вместимость необязательна; если указана, то больше нуля.
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Вместимость",
    )

    def __str__(self):
        """Текстовое представление: «ауд. 301»."""
        return f"ауд. {self.number}"

    class Meta:
        ordering = ["number"]
        verbose_name = "Аудитория"
        verbose_name_plural = "Аудитории"
        constraints = [
            # Аналог CHECK (capacity IS NULL OR capacity > 0) из ПР7.
            models.CheckConstraint(
                condition=Q(capacity__isnull=True) | Q(capacity__gt=0),
                name="room_capacity_positive",
            ),
        ]
