"""Тип занятия получает список допустимых значений (TextChoices).

В базе данных ничего не меняется: хранятся те же строки, поэтому
преобразовывать существующие записи не нужно.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lessons", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lesson",
            name="lesson_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("лабораторная", "Лабораторная"),
                    ("лекция", "Лекция"),
                    ("практика", "Практика"),
                ],
                default="",
                max_length=50,
                verbose_name="Тип занятия",
            ),
        ),
    ]
