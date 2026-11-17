from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Teacher",
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
                    "full_name",
                    models.CharField(
                        max_length=200, unique=True, verbose_name="ФИО"
                    ),
                ),
                (
                    "surname",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Фамилия"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        default="",
                        max_length=254,
                        verbose_name="Электронная почта",
                    ),
                ),
            ],
            options={
                "verbose_name": "Преподаватель",
                "verbose_name_plural": "Преподаватели",
                "ordering": ["surname", "full_name"],
            },
        ),
    ]
