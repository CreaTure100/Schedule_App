"""Тесты поиска свободных аудиторий (запуск: manage.py test)."""

from django.test import TestCase

from lessons.factories import make_lesson


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
