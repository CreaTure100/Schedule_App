"""Тесты поиска свободных аудиторий (запуск: manage.py test)."""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from lessons.factories import make_lesson
from lessons.models import Lesson
from rooms.models import Room


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
