"""Тесты моделей Django ORM и переноса данных (запуск: manage.py test)."""

import json
import tempfile
from datetime import time
from pathlib import Path

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from db.import_json import import_schedule
from db.import_sqlite_to_orm import import_data
from lessons.factories import make_lesson
from lessons.models import Lesson, Subject
from rooms.models import Room
from teachers.models import Teacher

SOURCE = [
    {"day": "Понедельник", "time": "09:00", "subject": "Математика",
     "teacher": "Иванов И.И.", "room": "301"},
    {"day": "Вторник", "time": "10:45",
     "subject": "Химия (лабораторная)",
     "teacher": "Петров П.П.", "room": "302"},
]


class ModelTests(TestCase):
    """Модели, связи и операции CRUD."""

    def setUp(self):
        self.lesson = make_lesson("Понедельник", "09:00", "Математика",
                                  "Иванов И.И.", "301")

    def test_str_methods(self):
        self.assertEqual(str(self.lesson.teacher), "Иванов И.И.")
        self.assertEqual(str(self.lesson.room), "ауд. 301")
        self.assertEqual(str(self.lesson.subject), "Математика")
        self.assertEqual(str(self.lesson), "Понедельник 09:00 — Математика")

    def test_surname_is_filled_from_full_name(self):
        self.assertEqual(self.lesson.teacher.surname, "Иванов")

    def test_forward_and_reverse_relations(self):
        lesson = Lesson.objects.select_related("room", "teacher").get()
        self.assertEqual(lesson.room.number, "301")
        self.assertEqual(lesson.teacher.full_name, "Иванов И.И.")
        self.assertEqual(list(lesson.teacher.lessons.all()), [lesson])
        self.assertEqual(list(lesson.room.lessons.all()), [lesson])
        self.assertEqual(list(lesson.subject.lessons.all()), [lesson])

    def test_subject_label_with_lesson_type(self):
        lab = make_lesson("Вторник", "10:00", "Химия", "Петров П.П.",
                          "302", lesson_type="лабораторная")
        self.assertEqual(lab.subject_label, "Химия (лабораторная)")
        self.assertEqual(self.lesson.subject_label, "Математика")

    def test_create_update_delete(self):
        room = Room.objects.create(number="404", capacity=30)
        room.capacity = 35
        room.save()
        self.assertEqual(Room.objects.get(pk=room.pk).capacity, 35)
        room.delete()
        self.assertFalse(Room.objects.filter(number="404").exists())

    def test_get_raises_for_missing_record(self):
        with self.assertRaises(Room.DoesNotExist):
            Room.objects.get(number="999")

    def test_protect_forbids_deleting_used_room(self):
        with self.assertRaises(ProtectedError):
            self.lesson.room.delete()
        self.assertTrue(Room.objects.filter(number="301").exists())

    def test_room_and_teacher_cannot_have_two_lessons_at_once(self):
        other_subject = Subject.objects.create(title="Физика")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lesson.objects.create(
                day=1, start_time="09:00", subject=other_subject,
                teacher=Teacher.objects.create(full_name="Другой Д.Д."),
                room=self.lesson.room)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lesson.objects.create(
                day=1, start_time="09:00", subject=other_subject,
                teacher=self.lesson.teacher,
                room=Room.objects.create(number="999"))

    def test_invalid_day_and_capacity_are_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lesson.objects.create(
                day=7, start_time="10:00", subject=self.lesson.subject,
                teacher=self.lesson.teacher, room=self.lesson.room)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Room.objects.create(number="0", capacity=0)

    def test_default_ordering(self):
        make_lesson("Понедельник", "08:00", "Ранняя", "Петров П.П.", "302")
        make_lesson("Вторник", "08:00", "Вторничная", "Петров П.П.", "303")
        titles = [item.subject.title for item in
                  Lesson.objects.select_related("subject")]
        self.assertEqual(titles, ["Ранняя", "Математика", "Вторничная"])

    def test_timestamps_from_abstract_model(self):
        self.assertIsNotNone(self.lesson.created_at)
        self.assertIsNotNone(self.lesson.updated_at)


class ImportFromSourceTests(TestCase):
    """Перенос данных из исходной базы ПР7 (db/import_sqlite_to_orm.py)."""

    def make_source(self, tmp):
        json_path = Path(tmp) / "schedule.json"
        json_path.write_text(json.dumps(SOURCE, ensure_ascii=False),
                             encoding="utf-8")
        source = Path(tmp) / "source.sqlite"
        import_schedule(json_path, source)
        return source

    def test_data_and_relations_are_transferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            counts = import_data(self.make_source(tmp))
        self.assertEqual(counts, {"teachers": 2, "rooms": 2,
                                  "subjects": 2, "lessons": 2})
        lab = Lesson.objects.select_related(
            "subject", "teacher", "room").get(subject__title="Химия")
        self.assertEqual(lab.lesson_type, "лабораторная")
        self.assertEqual(lab.start_time, time(10, 45))
        self.assertEqual(lab.get_day_display(), "Вторник")
        self.assertEqual(lab.teacher.full_name, "Петров П.П.")
        self.assertEqual(lab.room.number, "302")
        self.assertEqual(lab.teacher.email, "")

    def test_import_is_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.make_source(tmp)
            import_data(source)
            counts = import_data(source)
        self.assertEqual(counts["lessons"], 2)
        self.assertEqual(Lesson.objects.count(), 2)
