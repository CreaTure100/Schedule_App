"""Модели Django ORM «Предмет» и «Занятие» (ПР9).

Соответствуют таблицам subjects и lessons из ПР7 (sql/schema.sql).
Связи: у занятия один предмет, один преподаватель и одна аудитория
(ForeignKey), а у предмета, преподавателя и аудитории — много занятий
(обратный доступ subject.lessons, teacher.lessons, room.lessons).
"""

from django.db import models
from django.db.models import Case, CharField, Q, Value, When

from homepage.models import TimeStampedModel
from models import DAYS
from rooms.models import Room
from teachers.models import Teacher

# Дни недели хранятся числом 1..6, а на страницах показывается название:
# [(1, "Понедельник"), (2, "Вторник"), ...]. Число удобно сортировать.
DAY_CHOICES = list(enumerate(DAYS, 1))

# SQL-выражение CASE WHEN day = 1 THEN 'Понедельник' ... для запросов
# values(), где нет объектов модели и get_day_display() недоступен.
DAY_NAME = Case(
    *[When(day=number, then=Value(name)) for number, name in DAY_CHOICES],
    output_field=CharField(),
)


class Subject(TimeStampedModel):
    """Предмет (справочник): одно название хранится один раз."""

    title = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название предмета",
    )

    def __str__(self):
        """Текстовое представление: название предмета."""
        return self.title

    class Meta:
        ordering = ["title"]
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"


class LessonQuerySet(models.QuerySet):
    """Повторно используемые условия отбора занятий (ПР10).

    Методы возвращают QuerySet, поэтому их можно соединять цепочкой:
    Lesson.objects.on_day(1).laboratory().with_related(). Те же методы
    доступны и через обратные связи (room.lessons.on_day(2)).
    """

    def on_day(self, day_number):
        """Занятия указанного дня недели (1 — понедельник … 6)."""
        return self.filter(day=day_number)

    def for_teacher(self, teacher_id):
        """Занятия одного преподавателя."""
        return self.filter(teacher_id=teacher_id)

    def for_room(self, room_id):
        """Занятия в одной аудитории."""
        return self.filter(room_id=room_id)

    def at(self, day_number, start_time):
        """Занятия, начинающиеся в указанный день и время."""
        return self.filter(day=day_number, start_time=start_time)

    def laboratory(self):
        """Лабораторные занятия."""
        return self.filter(lesson_type=Lesson.LessonType.LABORATORY)

    def regular(self):
        """Занятия без указанного типа."""
        return self.filter(lesson_type="")

    def with_related(self):
        """Предмет, преподаватель и аудитория одним запросом (JOIN)."""
        return self.select_related("subject", "teacher", "room")


class Lesson(TimeStampedModel):
    """Занятие: день, время, предмет, преподаватель и аудитория."""

    class LessonType(models.TextChoices):
        """Тип занятия: в базе хранится код, на страницах — название."""

        LABORATORY = "лабораторная", "Лабораторная"
        LECTURE = "лекция", "Лекция"
        PRACTICE = "практика", "Практика"

    # Менеджер с методами LessonQuerySet: Lesson.objects.on_day(1).
    objects = LessonQuerySet.as_manager()

    # on_delete=PROTECT запрещает удалять предмет, преподавателя или
    # аудиторию, пока на них ссылаются занятия (как ON DELETE RESTRICT
    # в ПР7). related_name задаёт имя обратного доступа.
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="lessons",
        verbose_name="Предмет",
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="lessons",
        verbose_name="Преподаватель",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="lessons",
        verbose_name="Аудитория",
    )

    # День недели: число 1..6 с подписями из DAY_CHOICES.
    day = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        verbose_name="День недели",
    )

    # TimeField хранит время, а не произвольную строку.
    start_time = models.TimeField(
        verbose_name="Время начала",
    )

    duration_hours = models.FloatField(
        default=1.5,
        verbose_name="Длительность, ч",
    )

    # Тип занятия («лабораторная»); пустая строка — обычное занятие.
    # choices задают допустимые значения в формах и Django Admin; в базе
    # остаётся тот же текст, поэтому данные переносить не нужно.
    lesson_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        choices=LessonType.choices,
        verbose_name="Тип занятия",
    )

    @property
    def subject_label(self):
        """Название для страниц: «Химия (лабораторная)» или «Физика»."""
        if self.lesson_type:
            return f"{self.subject.title} ({self.lesson_type})"
        return self.subject.title

    def is_on_day(self, day_name):
        """Проходит ли занятие в указанный день недели (по названию)."""
        return self.get_day_display() == day_name

    def __str__(self):
        """Строка: день, время и название предмета."""
        return (f"{self.get_day_display()} {str(self.start_time)[:5]} — "
                f"{self.subject}")

    class Meta:
        # Сначала по дню недели, затем по времени, затем по ключу.
        ordering = ["day", "start_time", "pk"]
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
        constraints = [
            # Аналог CHECK-ограничений из ПР7.
            models.CheckConstraint(
                condition=Q(day__range=(1, len(DAYS))),
                name="lesson_day_valid",
            ),
            models.CheckConstraint(
                condition=Q(duration_hours__gt=0),
                name="lesson_duration_positive",
            ),
            # Аудитория и преподаватель не ведут два занятия сразу.
            models.UniqueConstraint(
                fields=["day", "start_time", "room"],
                name="unique_room_slot",
            ),
            models.UniqueConstraint(
                fields=["day", "start_time", "teacher"],
                name="unique_teacher_slot",
            ),
        ]
