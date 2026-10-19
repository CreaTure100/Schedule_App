"""Сквозные тесты веб-интерфейса (запуск: python manage.py test).

Данные берутся из временного data/schedule.json, поэтому тесты не
зависят от настоящего файла расписания. Часть проверок относится к
системе шаблонов (ПР6): наследование, include, статика, статус 404.
"""

import json
import os
import tempfile
from unittest.mock import patch

from django.test import SimpleTestCase

import homepage.views

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

    def test_static_files_are_linked(self):
        response = self.client.get("/")
        self.assertContains(response, "/static/homepage/css/style.css")
        self.assertContains(response, "/static/homepage/img/logo.png")
        self.assertContains(response, "/static/homepage/js/main.js")

    def test_pages_extend_base_and_include_parts(self):
        index = self.client.get("/")
        self.assertTemplateUsed(index, "homepage/index.html")
        self.assertTemplateUsed(index, "base.html")
        self.assertTemplateUsed(index, "includes/navigation.html")
        self.assertTemplateUsed(index, "homepage/includes/section_card.html")
        lessons = self.client.get("/lessons/")
        self.assertTemplateUsed(lessons, "lessons/lesson_list.html")
        self.assertTemplateUsed(lessons, "lessons/includes/lesson_card.html")
        self.assertTemplateUsed(lessons, "lessons/includes/lesson_status.html")

    def test_navigation_links_and_active_section(self):
        for url in ("/", "/lessons/", "/teachers/", "/rooms/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                for link in ("/", "/lessons/", "/teachers/", "/rooms/"):
                    self.assertContains(response, f'href="{link}"')
                self.assertContains(response, "nav-link active", count=1)

    def test_filters_show_counts(self):
        self.assertContains(self.client.get("/lessons/"),
                            "Всего занятий: 3")
        self.assertContains(self.client.get("/teachers/"),
                            "Всего преподавателей: 2")
        self.assertContains(self.client.get("/rooms/"),
                            "Всего аудиторий: 2")

    def test_today_lesson_is_highlighted(self):
        with patch("lessons.presenters.today_name",
                   return_value="Понедельник"):
            response = self.client.get("/lessons/")
        self.assertContains(response, "lesson-card--today", count=1)
        self.assertContains(response, "day-group--today", count=1)
        self.assertContains(response, ">сегодня</span>", count=1)

    def test_lessons_are_grouped_by_day(self):
        response = self.client.get("/lessons/")
        self.assertContains(response, "day-group__title", count=6)
        # дни без занятий (Четверг, Пятница, Суббота) помечены {% empty %}
        self.assertContains(response, "Занятий нет.", count=3)
        html = response.content.decode()
        positions = [html.index(f">{day}</h2>") for day in
                     ("Понедельник", "Вторник", "Среда", "Четверг",
                      "Пятница", "Суббота")]
        self.assertEqual(positions, sorted(positions))

    def test_lessons_inside_day_are_sorted_by_time(self):
        data = [
            {"day": "Понедельник", "time": "14:00", "subject": "Поздняя",
             "teacher": "Иванов И.И.", "room": "301"},
            {"day": "Вторник", "time": "09:00", "subject": "Вторничная",
             "teacher": "Иванов И.И.", "room": "301"},
            {"day": "Понедельник", "time": "9:00", "subject": "Ранняя",
             "teacher": "Иванов И.И.", "room": "301"},
        ]
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        html = self.client.get("/lessons/").content.decode()
        self.assertLess(html.index("Ранняя"), html.index("Поздняя"))
        self.assertLess(html.index("Поздняя"), html.index("Вторничная"))

    def test_empty_schedule_has_no_day_groups(self):
        os.remove(self.data_file)
        response = self.client.get("/lessons/")
        self.assertContains(response, "Расписание пусто")
        self.assertNotContains(response, "day-group__title")

    def test_static_files_are_served(self):
        for url, mime in (
                ("/static/homepage/img/logo.png", "image/png"),
                ("/static/homepage/css/style.css", "text/css"),
                ("/static/homepage/js/main.js", "text/javascript")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn(mime.split("/")[1],
                              response["Content-Type"])
                response.close()

    def test_page_titles(self):
        self.assertContains(self.client.get("/"),
                            "<title>Главная – Roomly</title>")
        self.assertContains(self.client.get("/rooms/1/"),
                            "<title>Аудитория 301 – Roomly</title>")

    def test_index_today_section(self):
        with patch("lessons.presenters.today_name",
                   return_value="Понедельник"):
            monday = self.client.get("/")
        self.assertContains(monday, "Занятия сегодня")
        self.assertContains(monday, "lesson-card--today", count=1)
        with patch("lessons.presenters.today_name", return_value=""):
            sunday = self.client.get("/")
        self.assertContains(sunday, "Сегодня занятий нет.")
        self.assertNotContains(sunday, "lesson-card--today")

    def test_room_and_teacher_status(self):
        with patch("lessons.presenters.today_name",
                   return_value="Понедельник"):
            rooms = self.client.get("/rooms/")
            teachers = self.client.get("/teachers/")
        self.assertContains(rooms, "Сегодня занята: 1")
        self.assertContains(rooms, "Сегодня свободна")
        self.assertContains(teachers, "Сегодня занятий: 1")
        self.assertContains(teachers, "Сегодня занятий нет")

    def test_empty_collections(self):
        os.remove(self.data_file)
        self.assertContains(self.client.get("/lessons/"), "Расписание пусто")
        self.assertContains(self.client.get("/teachers/"),
                            "Преподавателей пока нет")
        self.assertContains(self.client.get("/rooms/"),
                            "Аудиторий пока нет")

    def test_missing_object_status_and_template(self):
        response = self.client.get("/lessons/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "lessons/lesson_detail.html")
        self.assertContains(response, "№9999", status_code=404)

    def test_404_handler_uses_template(self):
        response = self.client.get("/нет-такой-страницы/")
        self.assertTemplateUsed(response, "homepage/not_found.html")

    def test_page_helper_is_removed(self):
        self.assertFalse(hasattr(homepage.views, "page"))
