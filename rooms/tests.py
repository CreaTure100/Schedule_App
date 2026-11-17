"""Тесты поиска свободных аудиторий (запуск: manage.py test)."""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from lessons.factories import make_lesson
from lessons.models import Lesson
from rooms.forms import RoomForm
from rooms.models import Room


def make_image(name="room.png", fmt="PNG"):
    """Маленькая настоящая картинка для загрузки в форму."""
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, fmt)
    return SimpleUploadedFile(
        name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


class FreeRoomsTests(TestCase):
    """Страница /rooms/free/: exclude() занятых аудиторий."""

    @classmethod
    def setUpTestData(cls):
        make_lesson("Понедельник", "09:00", "Математика",
                    "Иванов И.И.", "301")
        make_lesson("Понедельник", "09:00", "Физика",
                    "Петров П.П.", "302")
        make_lesson("Вторник", "09:00", "Химия", "Иванов И.И.", "303")

    def search(self, **params):
        return self.client.get("/rooms/free/", params)

    def test_form_without_params_shows_hint(self):
        response = self.search()
        self.assertContains(response, "<form")
        self.assertContains(response, "Задайте день и время")

    def test_busy_rooms_are_excluded(self):
        response = self.search(day="Понедельник", time="09:00")
        self.assertContains(response, "ауд. 303")
        self.assertNotContains(response, "ауд. 301")
        self.assertNotContains(response, "ауд. 302")

    def test_all_rooms_free_at_other_time(self):
        response = self.search(day="Понедельник", time="12:00")
        for number in ("301", "302", "303"):
            self.assertContains(response, f"ауд. {number}")

    def test_no_free_rooms_message(self):
        make_lesson("Среда", "09:00", "А", "Иванов И.И.", "301")
        make_lesson("Среда", "09:00", "Б", "Петров П.П.", "302")
        make_lesson("Среда", "09:00", "В", "Сидоров С.С.", "303")
        response = self.search(day="Среда", time="09:00")
        self.assertContains(response, "свободных аудиторий нет")

    def test_invalid_input_shows_error(self):
        for params in ({"day": "Foo", "time": "09:00"},
                       {"day": "Понедельник", "time": "25:99"},
                       {"day": "Понедельник", "time": ""},
                       {"time": "09:00"}):
            with self.subTest(params=params):
                response = self.search(**params)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "alert-warning")


class RoomModelTests(TestCase):
    """Slug, get_absolute_url() и вычисляемое поле is_large (ПР10)."""

    def test_slug_is_generated_on_create(self):
        room = Room.objects.create(number="301")
        room.refresh_from_db()
        self.assertEqual(room.slug, f"auditoriya-301-{room.pk}")

    def test_slug_transliterates_cyrillic_number(self):
        room = Room.objects.create(number="12а")
        self.assertEqual(room.slug, f"auditoriya-12a-{room.pk}")

    def test_slug_is_stable_after_number_change(self):
        room = Room.objects.create(number="301")
        old_slug = room.slug
        room.number = "302"
        room.save()
        room.refresh_from_db()
        self.assertEqual(room.slug, old_slug)

    def test_get_absolute_url_uses_named_route(self):
        room = Room.objects.create(number="301")
        self.assertEqual(room.get_absolute_url(),
                         reverse("rooms:slug_detail",
                                 kwargs={"slug": room.slug}))
        self.assertEqual(room.get_absolute_url(), f"/rooms/{room.slug}/")

    def test_is_large_is_calculated_by_database(self):
        room = Room.objects.create(number="301", capacity=30)
        room.refresh_from_db()
        self.assertFalse(room.is_large)
        room.capacity = 60
        room.save()
        room.refresh_from_db()
        self.assertTrue(room.is_large)

    def test_is_large_false_without_capacity(self):
        room = Room.objects.create(number="301")
        room.refresh_from_db()
        self.assertFalse(room.is_large)
        self.assertEqual(Room.objects.filter(is_large=True).count(), 0)


class RoomBySlugTests(TestCase):
    """Страница аудитории по slug и прежний адрес по номеру ключа."""

    @classmethod
    def setUpTestData(cls):
        make_lesson("Понедельник", "09:00", "Математика",
                    "Иванов И.И.", "301")
        cls.room = Room.objects.get(number="301")

    def test_page_opens_by_slug(self):
        response = self.client.get(self.room.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Аудитория 301")
        self.assertContains(response, "Математика")

    def test_old_numeric_route_still_works(self):
        response = self.client.get(f"/rooms/{self.room.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Аудитория 301")

    def test_unknown_slug_returns_404(self):
        response = self.client.get("/rooms/net-takoy-auditorii/")
        self.assertEqual(response.status_code, 404)

    def test_list_links_to_slug_url(self):
        response = self.client.get("/rooms/")
        self.assertContains(response, f'href="{self.room.get_absolute_url()}"')


class ContextProcessorTests(TestCase):
    """room_context: общие данные во всех шаблонах (ПР10)."""

    def test_site_name_and_rooms_total_on_several_pages(self):
        make_lesson("Понедельник", "09:00", "Математика",
                    "Иванов И.И.", "301")
        make_lesson("Понедельник", "10:00", "Физика",
                    "Иванов И.И.", "302")
        for url in ("/", "/lessons/", "/teachers/", "/rooms/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.context["site_name"], "Roomly")
                self.assertEqual(response.context["rooms_total"], 2)
                self.assertContains(response, "аудиторий в базе — 2")


class RoomAdminTests(TestCase):
    """Django Admin: списки, поиск, фильтры, inline и ссылка на сайт."""

    @classmethod
    def setUpTestData(cls):
        make_lesson("Понедельник", "09:00", "Математика",
                    "Иванов И.И.", "301", lesson_type="лабораторная")
        make_lesson("Вторник", "10:00", "Физика", "Петров П.П.", "302")
        cls.room = Room.objects.get(number="301")
        cls.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "password")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_admin_requires_login(self):
        self.client.logout()
        response = self.client.get("/admin/rooms/room/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_all_changelists_open(self):
        for url in ("/admin/", "/admin/rooms/room/",
                    "/admin/teachers/teacher/",
                    "/admin/lessons/subject/", "/admin/lessons/lesson/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_app_and_model_names_are_russian(self):
        response = self.client.get("/admin/")
        for text in ("Аудитории", "Преподаватели", "Занятия",
                     "Roomly: администрирование"):
            self.assertContains(response, text)

    def test_room_search_by_number(self):
        response = self.client.get("/admin/rooms/room/", {"q": "302"})
        other = Room.objects.get(number="302")
        self.assertContains(response, f"/admin/rooms/room/{other.pk}/change/")
        self.assertNotContains(
            response, f"/admin/rooms/room/{self.room.pk}/change/")

    def test_room_filter_by_is_large(self):
        Room.objects.filter(pk=self.room.pk).update(capacity=80)
        response = self.client.get(
            "/admin/rooms/room/", {"is_large__exact": 1})
        self.assertContains(response, "301")

    def test_room_change_page_shows_lessons_inline(self):
        response = self.client.get(f"/admin/rooms/room/{self.room.pk}/change/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Занятия в аудитории")
        self.assertContains(response, self.room.slug)

    def test_lesson_search_by_related_fields(self):
        response = self.client.get("/admin/lessons/lesson/",
                                   {"q": "Петров"})
        self.assertContains(response, "Физика")
        self.assertNotContains(response, "Математика")

    def test_lesson_filter_by_type(self):
        response = self.client.get("/admin/lessons/lesson/",
                                   {"lesson_type": "лабораторная"})
        self.assertContains(response, "Математика")
        self.assertNotContains(response, "Физика")

    def test_view_on_site_link_leads_to_public_page(self):
        content_type = ContentType.objects.get_for_model(Room)
        response = self.client.get(
            f"/admin/r/{content_type.pk}/{self.room.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith(
            self.room.get_absolute_url()))

    def test_mark_laboratory_action(self):
        lesson = Lesson.objects.get(subject__title="Физика")
        self.client.post("/admin/lessons/lesson/", {
            "action": "mark_laboratory",
            "_selected_action": [lesson.pk],
        })
        lesson.refresh_from_db()
        self.assertEqual(lesson.lesson_type, Lesson.LessonType.LABORATORY)


class FreeRoomsCancelledTests(TestCase):
    """Отменённое занятие не занимает аудиторию (ПР11)."""

    def test_cancelled_lesson_frees_room(self):
        lesson = make_lesson("Понедельник", "09:00", "Математика",
                             "Иванов И.И.", "301")
        busy = self.client.get(
            "/rooms/free/", {"day": "Понедельник", "time": "09:00"})
        self.assertNotContains(busy, "ауд. 301")
        lesson.cancel()
        free = self.client.get(
            "/rooms/free/", {"day": "Понедельник", "time": "09:00"})
        self.assertContains(free, "ауд. 301")

    def test_counters_ignore_cancelled_lessons(self):
        lesson = make_lesson("Понедельник", "09:00", "Математика",
                             "Иванов И.И.", "301")
        lesson.cancel()
        self.assertContains(self.client.get("/rooms/"),
                            "Занятий в расписании: 0")
        self.assertContains(self.client.get("/teachers/"),
                            "Занятий в расписании: 0")


class RoomFormTests(TestCase):
    """Форма RoomForm (ПР11)."""

    def test_valid_form_without_image(self):
        form = RoomForm({"number": "401", "floor": 4, "capacity": 30})
        self.assertTrue(form.is_valid(), form.errors)
        room = form.save()
        self.assertTrue(room.slug.startswith("auditoriya-401-"))
        self.assertFalse(room.image)

    def test_service_fields_are_not_in_form(self):
        fields = RoomForm().fields
        self.assertNotIn("slug", fields)
        self.assertNotIn("is_large", fields)

    def test_number_validation(self):
        for value in ("", "30 1", "<b>"):
            with self.subTest(value=value):
                form = RoomForm({"number": value})
                self.assertFalse(form.is_valid())
                self.assertIn("number", form.errors)
        self.assertEqual(
            RoomForm({"number": "<b>"}).errors["number"],
            ["Номер может содержать только буквы, цифры и дефис."])
        self.assertTrue(RoomForm({"number": "12а"}).is_valid())

    def test_duplicate_number_is_rejected(self):
        Room.objects.create(number="301")
        form = RoomForm({"number": "301"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["number"],
                         ["Аудитория с таким номером уже есть."])

    def test_capacity_must_be_positive(self):
        form = RoomForm({"number": "401", "capacity": 0})
        self.assertFalse(form.is_valid())
        self.assertIn("capacity", form.errors)

    def test_valid_image_is_accepted(self):
        form = RoomForm({"number": "401"}, {"image": make_image()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_unsupported_format_is_rejected(self):
        form = RoomForm({"number": "401"},
                        {"image": make_image("room.bmp", "BMP")})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_not_an_image_is_rejected(self):
        fake = SimpleUploadedFile("room.png", b"not an image",
                                  content_type="image/png")
        form = RoomForm({"number": "401"}, {"image": fake})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_big_file_is_rejected(self):
        with patch("rooms.forms.MAX_IMAGE_SIZE", 10):
            form = RoomForm({"number": "401"}, {"image": make_image()})
            self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["image"],
                         ["Файл слишком большой: не более 2 МБ."])


class RoomViewsTests(TestCase):
    """Создание и редактирование аудитории, загрузка изображения."""

    def setUp(self):
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.media_root = Path(media.name)
        override = override_settings(MEDIA_ROOT=media.name)
        override.enable()
        self.addCleanup(override.disable)

    def test_create_page_uses_multipart_form(self):
        response = self.client.get("/rooms/create/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rooms/room_form.html")
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_create_with_image_saves_file_and_shows_it(self):
        response = self.client.post("/rooms/create/", {
            "number": "401", "floor": 4, "capacity": 30,
            "image": make_image()})
        room = Room.objects.get(number="401")
        self.assertRedirects(response, room.get_absolute_url())
        self.assertTrue(room.image.name.startswith("rooms/"))
        self.assertEqual(len(list((self.media_root / "rooms").iterdir())), 1)
        page = self.client.get(room.get_absolute_url())
        self.assertContains(page, f'src="{room.image.url}"')
        file_response = self.client.get(room.image.url)
        self.assertEqual(file_response.status_code, 200)
        file_response.close()

    def test_room_without_image_shows_message(self):
        self.client.post("/rooms/create/", {"number": "401"})
        room = Room.objects.get(number="401")
        self.assertContains(self.client.get(room.get_absolute_url()),
                            "Изображение не загружено.")

    def test_create_with_invalid_data_shows_errors(self):
        Room.objects.create(number="301")
        response = self.client.post("/rooms/create/", {"number": "301"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Аудитория с таким номером уже есть.")
        self.assertEqual(Room.objects.count(), 1)

    def test_update_changes_room_and_keeps_image(self):
        room = Room.objects.create(number="401", image=make_image())
        old_name = room.image.name
        response = self.client.post(f"/rooms/{room.pk}/edit/", {
            "number": "402", "capacity": 40})
        self.assertRedirects(response, room.get_absolute_url())
        room.refresh_from_db()
        self.assertEqual(room.number, "402")
        self.assertEqual(room.image.name, old_name)
        self.assertEqual(Room.objects.count(), 1)

    def test_update_replaces_and_clears_image(self):
        room = Room.objects.create(number="401", image=make_image())
        old_name = room.image.name
        self.client.post(f"/rooms/{room.pk}/edit/", {
            "number": "401", "image": make_image("new.png")})
        room.refresh_from_db()
        self.assertNotEqual(room.image.name, old_name)
        self.client.post(f"/rooms/{room.pk}/edit/", {
            "number": "401", "image-clear": "on"})
        room.refresh_from_db()
        self.assertFalse(room.image)

    def test_update_page_is_filled_and_missing_room_is_404(self):
        room = Room.objects.create(number="401", floor=4)
        response = self.client.get(f"/rooms/{room.pk}/edit/")
        self.assertEqual(response.context["form"].instance, room)
        self.assertContains(response, 'value="401"')
        self.assertEqual(
            self.client.get("/rooms/999999/edit/").status_code, 404)

    def test_create_route_is_not_taken_for_slug(self):
        response = self.client.get("/rooms/create/")
        self.assertNotEqual(response.status_code, 404)

    def test_list_and_detail_have_action_links(self):
        room = Room.objects.create(number="401")
        self.assertContains(self.client.get("/rooms/"),
                            'href="/rooms/create/"')
        detail = self.client.get(room.get_absolute_url())
        self.assertContains(detail, f'href="/rooms/{room.pk}/edit/"')
        self.assertContains(detail, f"/lessons/create/?room={room.pk}")

    def test_admin_change_page_has_image_field(self):
        admin = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "password")
        self.client.force_login(admin)
        room = Room.objects.create(number="401")
        response = self.client.get(f"/admin/rooms/room/{room.pk}/change/")
        self.assertContains(response, 'name="image"')
