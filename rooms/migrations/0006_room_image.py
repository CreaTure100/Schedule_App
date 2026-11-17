"""Изображение аудитории (ПР11): поле ImageField (нужна Pillow)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0005_room_is_large"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="rooms/",
                verbose_name="Изображение",
            ),
        ),
    ]
