import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("rooms", "0001_initial"),
        ("teachers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subject",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Создано"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Изменено"
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        max_length=200,
                        unique=True,
                        verbose_name="Название предмета",
                    ),
                ),
            ],
            options={
                "verbose_name": "Предмет",
                "verbose_name_plural": "Предметы",
                "ordering": ["title"],
            },
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Создано"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Изменено"
                    ),
                ),
                (
                    "day",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Понедельник"),
                            (2, "Вторник"),
                            (3, "Среда"),
                            (4, "Четверг"),
                            (5, "Пятница"),
                            (6, "Суббота"),
                        ],
                        verbose_name="День недели",
                    ),
                ),
                (
                    "start_time",
                    models.TimeField(verbose_name="Время начала"),
                ),
                (
                    "duration_hours",
                    models.FloatField(
                        default=1.5, verbose_name="Длительность, ч"
                    ),
                ),
                (
                    "lesson_type",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=50,
                        verbose_name="Тип занятия",
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lessons",
                        to="rooms.room",
                        verbose_name="Аудитория",
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lessons",
                        to="lessons.subject",
                        verbose_name="Предмет",
                    ),
                ),
                (
                    "teacher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lessons",
                        to="teachers.teacher",
                        verbose_name="Преподаватель",
                    ),
                ),
            ],
            options={
                "verbose_name": "Занятие",
                "verbose_name_plural": "Занятия",
                "ordering": ["day", "start_time", "pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("day__range", (1, 6))),
                        name="lesson_day_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("duration_hours__gt", 0)),
                        name="lesson_duration_positive",
                    ),
                    models.UniqueConstraint(
                        fields=("day", "start_time", "room"),
                        name="unique_room_slot",
                    ),
                    models.UniqueConstraint(
                        fields=("day", "start_time", "teacher"),
                        name="unique_teacher_slot",
                    ),
                ],
            },
        ),
    ]
