"""Шаг 1 из 3: поле slug (пока без уникальности, со значением по умолчанию)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="slug",
            field=models.SlugField(
                blank=True,
                default="",
                editable=False,
                max_length=180,
                verbose_name="URL-идентификатор",
            ),
        ),
    ]
