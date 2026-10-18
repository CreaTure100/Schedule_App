"""Сквозные тесты веб-интерфейса (запуск: python manage.py test).

Данные берутся из временного data/schedule.json, поэтому тесты не
зависят от настоящего файла расписания.
"""

import json
import os
import tempfile

from django.test import SimpleTestCase

DATA = [
    {"day": "Понедельник", "time": "09:00", "subject": "Математика",
     "teacher": "Иванов И.И.", "room": "301"},
    {"day": "Вторник", "time": "10:00", "subject": "Физика",
     "teacher": "Иванов И.И.", "room": "302"},
    {"day": "Среда", "time": "11:00", "subject": "<script>alert(1)</script>",
     "teacher": "Петров П.П.", "room": "301"},
]


class SiteTests(SimpleTestCase):
    """Проверки страниц сайта на временных данных."""

    def setUp(self):
        old_cwd = os.getcwd()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, old_cwd)
        self.data_file = os.path.join(tmp.name, "data", "schedule.json")
        os.makedirs(os.path.dirname(self.data_file))
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False)
        os.chdir(tmp.name)

    def test_index(self):
        response = self.client.get("/")
        self.assertContains(response, "Расписание занятий")
        self.assertContains(response, "bootstrap@5.3")
        self.assertContains(response, "Данные загружены")

    def test_index_with_empty_schedule(self):
        os.remove(self.data_file)
        self.assertContains(self.client.get("/"), "Расписание пусто")

    def test_lesson_list_and_detail(self):
        response = self.client.get("/lessons/")
        self.assertContains(response, "Математика")
        self.assertContains(response, 'href="/lessons/2/"')
        detail = self.client.get("/lessons/1/")
        self.assertContains(detail, "Иванов И.И.")
        self.assertContains(detail, 'href="/teachers/1/"')
        self.assertContains(detail, 'href="/rooms/1/"')

    def test_teacher_pages(self):
        self.assertContains(self.client.get("/teachers/"), "Петров П.П.")
        detail = self.client.get("/teachers/1/")
        self.assertContains(detail, "Математика")
        self.assertContains(detail, "Физика")
        self.assertNotContains(detail, "alert(1)")

    def test_room_pages(self):
        self.assertContains(self.client.get("/rooms/"), "ауд. 302")
        detail = self.client.get("/rooms/1/")
        self.assertContains(detail, "Математика")
        self.assertNotContains(detail, "Физика")

    def test_missing_objects_return_404(self):
        for url in ("/lessons/99/", "/lessons/0/", "/teachers/99/",
                    "/rooms/99/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "не найден", status_code=404)

    def test_unknown_url_uses_custom_404(self):
        response = self.client.get("/нет-такой-страницы/")
        self.assertContains(response, "Такой страницы не существует",
                            status_code=404)

    def test_html_is_escaped(self):
        response = self.client.get("/lessons/")
        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")
