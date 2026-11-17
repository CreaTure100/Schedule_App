"""Шаг 3 из 3: после заполнения slug делаем его уникальным."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0003_populate_room_slugs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="slug",
            field=models.SlugField(
                blank=True,
                editable=False,
                max_length=180,
                unique=True,
                verbose_name="URL-идентификатор",
            ),
        ),
    ]
