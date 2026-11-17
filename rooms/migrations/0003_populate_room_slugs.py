"""Шаг 2 из 3: миграция данных — slug для уже существующих аудиторий."""

from django.db import migrations

from rooms.slugs import build_room_slug


def populate_room_slugs(apps, schema_editor):
    """Заполнить slug у аудиторий, у которых он пуст."""
    # Историческая модель: состояние таблицы на момент этой миграции.
    Room = apps.get_model("rooms", "Room")
    for room in Room.objects.filter(slug="").order_by("pk"):
        room.slug = build_room_slug(room.number, room.pk)
        room.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0002_room_slug"),
    ]

    operations = [
        # Обратное действие не требуется: поле slug удаляется миграцией 0002.
        migrations.RunPython(populate_room_slugs, migrations.RunPython.noop),
    ]
