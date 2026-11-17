import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Room",
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
                    "number",
                    models.CharField(
                        max_length=20,
                        unique=True,
                        verbose_name="Номер аудитории",
                    ),
                ),
                (
                    "floor",
                    models.PositiveSmallIntegerField(
                        blank=True, null=True, verbose_name="Этаж"
                    ),
                ),
                (
                    "capacity",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="Вместимость",
                    ),
                ),
            ],
            options={
                "verbose_name": "Аудитория",
                "verbose_name_plural": "Аудитории",
                "ordering": ["number"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("capacity__isnull", True),
                            ("capacity__gt", 0),
                            _connector="OR",
                        ),
                        name="room_capacity_positive",
                    )
                ],
            },
        ),
    ]
