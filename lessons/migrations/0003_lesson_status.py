"""Статус занятия (ПР11): отмена занятия без удаления записи.

Поле status получает значение «active» у всех существующих занятий.
Ограничения «аудитория/преподаватель + день + время» становятся
условными: они действуют только для занятий со статусом «active», чтобы
отменённое занятие не блокировало аудиторию и преподавателя.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lessons", "0002_alter_lesson_lesson_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Проводится"),
                    ("cancelled", "Отменено"),
                ],
                default="active",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="lesson",
            name="unique_room_slot",
        ),
        migrations.RemoveConstraint(
            model_name="lesson",
            name="unique_teacher_slot",
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("day", "start_time", "room"),
                name="unique_active_room_slot",
                violation_error_message=(
                    "В это время аудитория занята другим занятием."
                ),
            ),
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("day", "start_time", "teacher"),
                name="unique_active_teacher_slot",
                violation_error_message=(
                    "В это время преподаватель ведёт другое занятие."
                ),
            ),
        ),
    ]
