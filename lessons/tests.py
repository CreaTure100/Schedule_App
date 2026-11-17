"""Тесты моделей Django ORM и переноса данных (запуск: manage.py test)."""

import json
import tempfile
from datetime import time
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import Client, TestCase

from db.import_json import import_schedule
from db.import_sqlite_to_orm import import_data
from lessons.factories import make_lesson
from lessons.forms import LessonForm
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


class LessonQuerySetTests(TestCase):
    """Методы LessonQuerySet и перечисление LessonType (ПР10)."""

    @classmethod
    def setUpTestData(cls):
        cls.mon_lab = make_lesson("Понедельник", "09:00", "Химия",
                                  "Иванов И.И.", "301",
                                  lesson_type="лабораторная")
        cls.mon = make_lesson("Понедельник", "11:00", "Физика",
                              "Петров П.П.", "302")
        cls.tue = make_lesson("Вторник", "09:00", "Алгебра",
                              "Иванов И.И.", "302")

    def test_on_day(self):
        self.assertCountEqual(Lesson.objects.on_day(1),
                              [self.mon_lab, self.mon])
        self.assertCountEqual(Lesson.objects.on_day(2), [self.tue])
        self.assertCountEqual(Lesson.objects.on_day(6), [])

    def test_for_teacher_and_for_room(self):
        ivanov = Teacher.objects.get(full_name="Иванов И.И.")
        room = Room.objects.get(number="302")
        self.assertCountEqual(Lesson.objects.for_teacher(ivanov.pk),
                              [self.mon_lab, self.tue])
        self.assertCountEqual(Lesson.objects.for_room(room.pk),
                              [self.mon, self.tue])

    def test_at_finds_exact_slot(self):
        self.assertCountEqual(Lesson.objects.at(1, "09:00"), [self.mon_lab])
        self.assertCountEqual(Lesson.objects.at(2, "11:00"), [])

    def test_laboratory_and_regular(self):
        self.assertCountEqual(Lesson.objects.laboratory(), [self.mon_lab])
        self.assertCountEqual(Lesson.objects.regular(),
                              [self.mon, self.tue])

    def test_methods_are_chainable(self):
        found = Lesson.objects.on_day(1).laboratory().with_related()
        self.assertCountEqual(found, [self.mon_lab])

    def test_available_through_related_manager(self):
        room = Room.objects.get(number="302")
        self.assertCountEqual(room.lessons.on_day(2), [self.tue])

    def test_with_related_avoids_extra_queries(self):
        with self.assertNumQueries(1):
            for lesson in Lesson.objects.with_related():
                str(lesson.subject), str(lesson.teacher), str(lesson.room)

    def test_lesson_type_choices_and_display(self):
        self.assertEqual(Lesson.LessonType.LABORATORY.value, "лабораторная")
        self.assertEqual(self.mon_lab.get_lesson_type_display(),
                         "Лабораторная")
        self.assertEqual(self.mon.get_lesson_type_display(), "")

    def test_stats_page_counts_lesson_types(self):
        response = self.client.get("/db/stats/")
        self.assertEqual(response.context["summary"]["laboratory_count"], 1)
        self.assertEqual(response.context["summary"]["regular_count"], 2)


class LessonStatusTests(TestCase):
    """Статус занятия, cancel() и active() (ПР11)."""

    def setUp(self):
        self.lesson = make_lesson("Понедельник", "09:00", "Математика",
                                  "Иванов И.И.", "301")

    def test_new_lesson_is_active_by_default(self):
        self.assertEqual(self.lesson.status, Lesson.Status.ACTIVE)
        self.assertTrue(self.lesson.is_active)
        self.assertEqual(self.lesson.get_status_display(), "Проводится")

    def test_cancel_changes_status_and_keeps_record(self):
        self.lesson.cancel()
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, Lesson.Status.CANCELLED)
        self.assertFalse(self.lesson.is_active)
        # Запись сохранилась, но среди проводимых её нет.
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(Lesson.objects.active().count(), 0)

    def test_cancel_updates_modification_time(self):
        before = self.lesson.updated_at
        self.lesson.cancel()
        self.lesson.refresh_from_db()
        self.assertGreaterEqual(self.lesson.updated_at, before)

    def test_active_is_chainable_with_other_methods(self):
        cancelled = make_lesson("Понедельник", "11:00", "Физика",
                                "Петров П.П.", "302",
                                status=Lesson.Status.CANCELLED)
        self.assertCountEqual(Lesson.objects.on_day(1),
                              [self.lesson, cancelled])
        self.assertCountEqual(Lesson.objects.active().on_day(1),
                              [self.lesson])

    def test_cancelled_lesson_does_not_block_room_and_teacher(self):
        self.lesson.cancel()
        other_subject = Subject.objects.create(title="Физика")
        # То же время, та же аудитория и тот же преподаватель: раньше
        # это был IntegrityError, теперь отменённое занятие не мешает.
        Lesson.objects.create(
            day=1, start_time="09:00", subject=other_subject,
            teacher=self.lesson.teacher, room=self.lesson.room)
        self.assertEqual(Lesson.objects.active().count(), 1)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_two_active_lessons_still_conflict(self):
        other_subject = Subject.objects.create(title="Физика")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lesson.objects.create(
                day=1, start_time="09:00", subject=other_subject,
                teacher=Teacher.objects.create(full_name="Другой Д.Д."),
                room=self.lesson.room)

    def test_models_match_migrations(self):
        """Миграции lessons и rooms описывают модели без расхождений."""
        try:
            call_command("makemigrations", "lessons", "rooms", "--check",
                         "--dry-run", verbosity=0, stdout=StringIO())
        except SystemExit:
            self.fail("Модели изменены без миграции: "
                      "выполните python manage.py makemigrations.")


class LessonFormTests(TestCase):
    """Форма LessonForm: поля, валидация и бизнес-правила (ПР11)."""

    @classmethod
    def setUpTestData(cls):
        cls.lesson = make_lesson("Понедельник", "09:00", "Математика",
                                 "Иванов И.И.", "301")
        cls.subject = Subject.objects.get(title="Математика")
        cls.other_teacher = Teacher.objects.create(full_name="Петров П.П.")
        cls.other_room = Room.objects.create(number="302")

    def data(self, **overrides):
        data = {
            "subject": self.subject.pk,
            "teacher": self.other_teacher.pk,
            "room": self.other_room.pk,
            "day": 2,
            "start_time": "10:00",
            "duration_hours": "1.5",
            "lesson_type": "",
        }
        data.update(overrides)
        return data

    def test_valid_form_creates_active_lesson(self):
        form = LessonForm(self.data())
        self.assertTrue(form.is_valid(), form.errors)
        lesson = form.save()
        self.assertEqual(lesson.status, Lesson.Status.ACTIVE)
        self.assertEqual(lesson.start_time, time(10, 0))
        self.assertEqual(Lesson.objects.count(), 2)

    def test_service_fields_are_not_in_form(self):
        fields = LessonForm().fields
        for name in ("status", "created_at", "updated_at"):
            self.assertNotIn(name, fields)

    def test_status_in_post_data_is_ignored(self):
        form = LessonForm(self.data(status="cancelled"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().status, Lesson.Status.ACTIVE)

    def test_required_fields(self):
        form = LessonForm({})
        self.assertFalse(form.is_valid())
        for name in ("subject", "teacher", "room", "day", "start_time",
                     "duration_hours"):
            self.assertIn(name, form.errors)
        self.assertNotIn("lesson_type", form.errors)

    def test_duration_validator(self):
        for value in ("0", "-1", "9"):
            with self.subTest(value=value):
                form = LessonForm(self.data(duration_hours=value))
                self.assertFalse(form.is_valid())
                self.assertIn("duration_hours", form.errors)
        self.assertEqual(
            LessonForm(self.data(duration_hours="0")).errors[
                "duration_hours"],
            ["Длительность должна быть больше нуля."])

    def test_start_time_must_be_in_study_hours(self):
        for value in ("07:59", "21:01", "00:30"):
            with self.subTest(value=value):
                form = LessonForm(self.data(start_time=value))
                self.assertFalse(form.is_valid())
                self.assertEqual(
                    form.errors["start_time"],
                    ["Занятие должно начинаться с 08:00 до 21:00."])
        for value in ("08:00", "21:00"):
            with self.subTest(value=value):
                self.assertTrue(
                    LessonForm(self.data(start_time=value)).is_valid())

    def test_invalid_day_and_type_are_rejected(self):
        self.assertIn("day", LessonForm(self.data(day=7)).errors)
        self.assertIn("day", LessonForm(self.data(day="abc")).errors)
        self.assertIn("lesson_type",
                      LessonForm(self.data(lesson_type="экзамен")).errors)

    def test_busy_room_is_rejected(self):
        form = LessonForm(self.data(day=1, start_time="09:00",
                                    room=self.lesson.room_id))
        self.assertFalse(form.is_valid())
        self.assertIn("В это время аудитория занята другим занятием.",
                      form.non_field_errors())
        self.assertEqual(Lesson.objects.count(), 1)

    def test_busy_teacher_is_rejected(self):
        form = LessonForm(self.data(day=1, start_time="09:00",
                                    teacher=self.lesson.teacher_id))
        self.assertFalse(form.is_valid())
        self.assertIn("В это время преподаватель ведёт другое занятие.",
                      form.non_field_errors())

    def test_cancelled_lesson_does_not_block_slot(self):
        self.lesson.cancel()
        form = LessonForm(self.data(day=1, start_time="09:00",
                                    room=self.lesson.room_id,
                                    teacher=self.lesson.teacher_id))
        self.assertTrue(form.is_valid(), form.errors)

    def test_lesson_does_not_conflict_with_itself_on_edit(self):
        form = LessonForm(
            self.data(day=1, start_time="09:00",
                      room=self.lesson.room_id,
                      teacher=self.lesson.teacher_id),
            instance=self.lesson)
        self.assertTrue(form.is_valid(), form.errors)

    def test_edit_into_busy_slot_is_rejected(self):
        make_lesson("Вторник", "10:00", "Физика", "Петров П.П.", "302")
        form = LessonForm(
            self.data(day=2, start_time="10:00",
                      room=self.other_room.pk,
                      teacher=self.lesson.teacher_id),
            instance=self.lesson)
        self.assertFalse(form.is_valid())
        self.assertIn("В это время аудитория занята другим занятием.",
                      form.non_field_errors())

    def test_edit_form_is_filled_from_instance(self):
        form = LessonForm(instance=self.lesson)
        self.assertEqual(form.initial["room"], self.lesson.room_id)
        self.assertEqual(form.initial["day"], 1)
        self.assertEqual(form.initial["start_time"], time(9, 0))


class LessonViewsTests(TestCase):
    """Создание, редактирование и отмена занятия в браузере (ПР11)."""

    @classmethod
    def setUpTestData(cls):
        cls.lesson = make_lesson("Понедельник", "09:00", "Математика",
                                 "Иванов И.И.", "301")
        cls.subject = Subject.objects.get(title="Математика")
        cls.other_teacher = Teacher.objects.create(full_name="Петров П.П.")
        cls.other_room = Room.objects.create(number="302")

    def payload(self, **overrides):
        data = {
            "subject": self.subject.pk,
            "teacher": self.other_teacher.pk,
            "room": self.other_room.pk,
            "day": 2,
            "start_time": "10:00",
            "duration_hours": "1.5",
            "lesson_type": "",
        }
        data.update(overrides)
        return data

    # ---- создание

    def test_create_page_shows_empty_form(self):
        response = self.client.get("/lessons/create/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lessons/lesson_form.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertFalse(response.context["form"].is_bound)
        self.assertContains(response, "Новое занятие")
        self.assertContains(response, "csrfmiddlewaretoken")
        for name in ("subject", "teacher", "room", "day", "start_time",
                     "duration_hours", "lesson_type"):
            self.assertContains(response, f'name="{name}"')
        self.assertNotContains(response, 'name="status"')

    def test_create_prefills_room_from_query(self):
        response = self.client.get(
            "/lessons/create/", {"room": self.other_room.pk})
        self.assertEqual(response.context["form"].initial["room"],
                         str(self.other_room.pk))
        garbage = self.client.get("/lessons/create/", {"room": "abc"})
        self.assertEqual(garbage.status_code, 200)
        self.assertNotIn("room", garbage.context["form"].initial)

    def test_create_saves_lesson_and_redirects_to_detail(self):
        response = self.client.post("/lessons/create/", self.payload())
        new = Lesson.objects.exclude(pk=self.lesson.pk).get()
        self.assertRedirects(response, f"/lessons/{new.pk}/")
        self.assertEqual(new.status, Lesson.Status.ACTIVE)
        self.assertEqual(new.room, self.other_room)
        self.assertEqual(new.start_time, time(10, 0))

    def test_create_shows_success_message(self):
        response = self.client.post("/lessons/create/", self.payload(),
                                    follow=True)
        self.assertContains(response, "Занятие добавлено в расписание.")

    def test_create_with_invalid_data_shows_errors_and_saves_nothing(self):
        response = self.client.post("/lessons/create/", self.payload(
            subject="", duration_hours="0"))
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("subject", form.errors)
        self.assertIn("duration_hours", form.errors)
        self.assertContains(response, "Длительность должна быть больше нуля.")
        self.assertEqual(Lesson.objects.count(), 1)

    def test_create_keeps_entered_values_after_error(self):
        response = self.client.post("/lessons/create/", self.payload(
            start_time="07:00"))
        self.assertContains(response, 'value="07:00"')
        self.assertContains(response, "Занятие должно начинаться с 08:00")

    def test_create_rejects_busy_room_and_teacher(self):
        busy_room = self.client.post("/lessons/create/", self.payload(
            day=1, start_time="09:00", room=self.lesson.room_id))
        self.assertContains(busy_room,
                            "В это время аудитория занята другим занятием.")
        busy_teacher = self.client.post("/lessons/create/", self.payload(
            day=1, start_time="09:00", teacher=self.lesson.teacher_id))
        self.assertContains(
            busy_teacher, "В это время преподаватель ведёт другое занятие.")
        self.assertEqual(Lesson.objects.count(), 1)

    def test_create_allowed_after_cancel(self):
        self.lesson.cancel()
        response = self.client.post("/lessons/create/", self.payload(
            day=1, start_time="09:00", room=self.lesson.room_id,
            teacher=self.lesson.teacher_id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Lesson.objects.active().count(), 1)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_database_conflict_is_reported_not_raised(self):
        # Гонка двух запросов: форма проверку прошла, а база отказала.
        with patch.object(LessonForm, "save", side_effect=IntegrityError):
            response = self.client.post("/lessons/create/", self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Не удалось сохранить занятие")

    # ---- редактирование

    def test_update_page_shows_current_values(self):
        response = self.client.get(f"/lessons/{self.lesson.pk}/edit/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance, self.lesson)
        self.assertContains(response, "Редактирование занятия")
        self.assertContains(response, 'value="09:00"')

    def test_update_changes_existing_record(self):
        response = self.client.post(
            f"/lessons/{self.lesson.pk}/edit/",
            self.payload(day=1, start_time="11:00",
                         teacher=self.lesson.teacher_id,
                         room=self.lesson.room_id))
        self.assertRedirects(response, f"/lessons/{self.lesson.pk}/")
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.start_time, time(11, 0))
        # Новая запись не появилась: изменён существующий объект.
        self.assertEqual(Lesson.objects.count(), 1)

    def test_update_without_changes_does_not_conflict_with_itself(self):
        response = self.client.post(
            f"/lessons/{self.lesson.pk}/edit/",
            self.payload(day=1, start_time="09:00",
                         teacher=self.lesson.teacher_id,
                         room=self.lesson.room_id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_update_into_busy_slot_is_rejected(self):
        make_lesson("Вторник", "10:00", "Физика", "Петров П.П.", "302")
        response = self.client.post(
            f"/lessons/{self.lesson.pk}/edit/",
            self.payload(day=2, start_time="10:00",
                         teacher=self.lesson.teacher_id,
                         room=self.other_room.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "В это время аудитория занята другим занятием.")
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.day, 1)

    def test_update_missing_or_cancelled_lesson_returns_404(self):
        self.assertEqual(
            self.client.get("/lessons/999999/edit/").status_code, 404)
        self.lesson.cancel()
        self.assertEqual(
            self.client.get(f"/lessons/{self.lesson.pk}/edit/").status_code,
            404)
        self.assertEqual(
            self.client.post(f"/lessons/{self.lesson.pk}/edit/",
                             self.payload()).status_code, 404)

    # ---- отмена

    def test_cancel_changes_status_and_redirects_to_list(self):
        response = self.client.post(f"/lessons/{self.lesson.pk}/cancel/")
        self.assertRedirects(response, "/lessons/")
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, Lesson.Status.CANCELLED)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.pk).exists())

    def test_cancel_shows_message(self):
        response = self.client.post(f"/lessons/{self.lesson.pk}/cancel/",
                                    follow=True)
        self.assertContains(response, "Занятие отменено.")

    def test_cancel_by_get_is_not_allowed(self):
        response = self.client.get(f"/lessons/{self.lesson.pk}/cancel/")
        self.assertEqual(response.status_code, 405)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, Lesson.Status.ACTIVE)

    def test_cancel_twice_or_missing_returns_404(self):
        url = f"/lessons/{self.lesson.pk}/cancel/"
        self.client.post(url)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(
            self.client.post("/lessons/999999/cancel/").status_code, 404)

    def test_cancel_is_protected_by_csrf_token(self):
        strict = Client(enforce_csrf_checks=True)
        response = strict.post(f"/lessons/{self.lesson.pk}/cancel/")
        self.assertEqual(response.status_code, 403)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, Lesson.Status.ACTIVE)

    def test_forms_contain_csrf_token(self):
        for url in (f"/lessons/{self.lesson.pk}/", "/lessons/create/",
                    f"/lessons/{self.lesson.pk}/edit/"):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url),
                                    "csrfmiddlewaretoken")

    def test_detail_page_has_edit_and_cancel_controls(self):
        response = self.client.get(f"/lessons/{self.lesson.pk}/")
        self.assertContains(
            response, f'href="/lessons/{self.lesson.pk}/edit/"')
        self.assertContains(
            response, f'action="/lessons/{self.lesson.pk}/cancel/"')

    def test_list_has_add_button(self):
        self.assertContains(self.client.get("/lessons/"),
                            'href="/lessons/create/"')

    # ---- отменённое занятие скрыто на всех страницах

    def test_cancelled_lesson_is_hidden_everywhere(self):
        self.lesson.cancel()
        self.assertNotContains(self.client.get("/lessons/"), "Математика")
        self.assertEqual(
            self.client.get(f"/lessons/{self.lesson.pk}/").status_code, 404)
        room_page = self.client.get(f"/rooms/{self.lesson.room_id}/")
        self.assertNotContains(room_page, "Математика")
        teacher_page = self.client.get(
            f"/teachers/{self.lesson.teacher_id}/")
        self.assertNotContains(teacher_page, "Математика")
        self.assertContains(self.client.get("/"), "Расписание пусто")
        self.assertContains(self.client.get("/db/lessons/"),
                            "Найдено занятий: 0")
        stats = self.client.get("/db/stats/")
        self.assertEqual(stats.context["summary"]["lessons_count"], 0)
        free = self.client.get("/rooms/free/",
                               {"day": "Понедельник", "time": "09:00"})
        self.assertContains(free, "ауд. 301")
