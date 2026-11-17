"""Модель Django ORM «Аудитория» (ПР9).

Соответствует таблице rooms из ПР7 (sql/schema.sql). Не путать с
классом models.Room из пакета models/ в корне проекта (ПР3).
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Q, Value, When
from django.urls import reverse

from homepage.models import TimeStampedModel
from rooms.slugs import build_room_slug

# Аудитория считается большой, если в неё помещается не менее
# стольких человек (учебный порог ПР10, п. 5.4.4 методички).
LARGE_ROOM_CAPACITY = 50


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

    # Вычисляемое поле: значение считает сама база данных (GeneratedField)
    # по вместимости и хранит его в таблице (db_persist=True). Вручную
    # поле не задаётся и не редактируется. Если вместимость не указана
    # (NULL), условие не выполняется и признак равен False.
    is_large = models.GeneratedField(
        expression=Case(
            When(capacity__gte=LARGE_ROOM_CAPACITY, then=Value(True)),
            default=Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="Большая аудитория",
    )

    # URL-идентификатор для адреса /rooms/<slug>/. Заполняется в save()
    # после получения первичного ключа и не меняется при смене номера:
    # ссылки на аудиторию остаются рабочими.
    slug = models.SlugField(
        max_length=180,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="URL-идентификатор",
    )

    def save(self, *args, **kwargs):
        """Сохранить аудиторию и при первом сохранении создать slug."""
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = build_room_slug(self.number, self.pk)
            # update() не вызывает save() повторно и не меняет updated_at.
            type(self).objects.filter(pk=self.pk).update(slug=self.slug)

    def get_absolute_url(self):
        """Адрес страницы аудитории по именованному маршруту.

        Django Admin использует этот метод для ссылки «Смотреть на
        сайте». Без slug (объект ещё не сохранён) возвращается адрес
        по числовому идентификатору.
        """
        if self.slug:
            return reverse("rooms:slug_detail", kwargs={"slug": self.slug})
        return reverse("rooms:detail", kwargs={"room_id": self.pk})

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
