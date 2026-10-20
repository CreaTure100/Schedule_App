"""Тесты страниц с данными из SQLite (запуск: python manage.py test).

Для каждого теста создаётся временная база: схема и импорт из
временного JSON, настоящий data/roomly.sqlite не затрагивается.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from db.import_json import import_schedule

DATA = [
    {"day": "Понедельник", "time": "09:00", "subject": "Математика",
     "teacher": "Иванов И.И.", "room": "301"},
    {"day": "Понедельник", "time": "11:00", "subject": "Физика",
     "teacher": "Иванов И.И.", "room": "302"},
    {"day": "Понедельник", "time": "13:00",
     "subject": "Химия (лабораторная)",
     "teacher": "Петров П.П.", "room": "303"},
    {"day": "Вторник", "time": "10:00", "subject": "Алгебра",
     "teacher": "Петров П.П.", "room": "301"},
    {"day": "Среда", "time": "11:00", "subject": "<script>alert(1)</script>",
     "teacher": "Сидоров С.С.", "room": "302"},
]
MONDAY_10 = datetime(2026, 10, 19, 10, 0)
SUNDAY_10 = datetime(2026, 10, 18, 10, 0)


class DbPagesTests(SimpleTestCase):
    """Страницы раздела «База данных»."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        json_path = Path(tmp.name) / "schedule.json"
        json_path.write_text(json.dumps(DATA, ensure_ascii=False),
                             encoding="utf-8")
        self.db_path = Path(tmp.name) / "roomly.sqlite"
        import_schedule(json_path, self.db_path)
        self.tmp = Path(tmp.name)
        override = override_settings(SQLITE_PATH=self.db_path)
        override.enable()
        self.addCleanup(override.disable)

    def test_lesson_list_uses_join_and_order(self):
        response = self.client.get("/db/lessons/")
        self.assertTemplateUsed(response, "dbpages/lesson_list.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "Иванов И.И.")
        self.assertContains(response, "лабораторная")
        html = response.content.decode()
        self.assertLess(html.index("Математика"), html.index("Алгебра"))
        self.assertLess(html.index("Алгебра"), html.index("alert"))
        self.assertContains(response, "Всего занятий: 5")

    def test_html_is_escaped(self):
        response = self.client.get("/db/lessons/")
        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

    def test_teacher_list_orders_by_surname(self):
        response = self.client.get("/db/teachers/")
        html = response.content.decode()
        self.assertLess(html.index("Иванов И.И."), html.index("Петров"))
        self.assertLess(html.index("Петров"), html.index("Сидоров"))
        self.assertContains(response, "не указан", count=3)

    def test_today_shows_only_upcoming_lessons(self):
        with patch("dbpages.views.now_local", return_value=MONDAY_10):
            response = self.client.get("/db/today/")
        self.assertContains(response, "Физика")
        self.assertContains(response, "Химия")
        self.assertNotContains(response, "Математика")
        self.assertNotContains(response, "Алгебра")
        self.assertContains(response, "Найдено занятий: 2")

    def test_today_on_sunday_is_empty(self):
        with patch("dbpages.views.now_local", return_value=SUNDAY_10):
            response = self.client.get("/db/today/")
        self.assertContains(response, "Воскресенье")
        self.assertContains(response, "Сегодня больше нет занятий")

    def test_search_form_without_criteria_shows_hint(self):
        response = self.client.get("/db/search/")
        self.assertContains(response, "<form")
        self.assertContains(response, 'action="/db/search/"')
        self.assertContains(response, "Задайте критерий")
        self.assertNotContains(response, "Иванов")

    def test_search_by_day(self):
        response = self.client.get("/db/search/", {"day": "Вторник"})
        self.assertContains(response, "Алгебра")
        self.assertNotContains(response, "Математика")
        self.assertContains(response, "Найдено занятий: 1")

    def test_search_by_teacher_ignores_case(self):
        response = self.client.get("/db/search/", {"teacher": "иВАНов"})
        self.assertContains(response, "Математика")
        self.assertContains(response, "Физика")
        self.assertNotContains(response, "Алгебра")

    def test_search_by_day_and_teacher(self):
        response = self.client.get(
            "/db/search/", {"day": "Понедельник", "teacher": "петров"})
        self.assertContains(response, "Химия")
        self.assertContains(response, "Найдено занятий: 1")

    def test_search_without_results_shows_empty_message(self):
        response = self.client.get("/db/search/", {"teacher": "Нет такого"})
        self.assertContains(response, "Ничего не найдено")

    def test_search_keeps_form_values(self):
        response = self.client.get(
            "/db/search/", {"day": "Среда", "teacher": "сидоров"})
        self.assertContains(response, 'value="сидоров"')
        self.assertContains(response, '<option value="Среда" selected>')

    def test_search_unknown_day_is_ignored(self):
        response = self.client.get("/db/search/", {"day": "Foo"})
        self.assertContains(response, "Задайте критерий")

    def test_search_is_safe_against_sql_injection(self):
        for value in ("' OR 1=1 --", "'; DROP TABLE lessons; --",
                      "%", "_"):
            with self.subTest(value=value):
                response = self.client.get("/db/search/",
                                           {"teacher": value})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Ничего не найдено")
        self.assertContains(self.client.get("/db/lessons/"), "Математика")

    def test_stats_page(self):
        response = self.client.get("/db/stats/")
        self.assertTemplateUsed(response, "dbpages/stats.html")
        self.assertContains(response, "Занятия по преподавателям")
        self.assertContains(response, "Петров П.П.")
        # HAVING COUNT(*) >= 2: аудитории 301 и 302, но не 303
        self.assertContains(response, "ауд. 301")
        self.assertContains(response, "ауд. 302")
        self.assertNotContains(response, "ауд. 303")
        self.assertContains(response, "Понедельник")

    def test_pages_show_sql_query(self):
        for url in ("/db/lessons/", "/db/teachers/", "/db/stats/"):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), "SELECT")

    def test_navigation_links_use_url_names(self):
        response = self.client.get("/")
        for link in ("/db/lessons/", "/db/teachers/", "/db/today/",
                     "/db/search/", "/db/stats/"):
            self.assertContains(response, f'href="{link}"')

    def test_navigation_marks_active_db_page(self):
        response = self.client.get("/db/stats/")
        self.assertContains(response, "dropdown-item active", count=1)
        self.assertContains(response, "dropdown-toggle active", count=1)
        index = self.client.get("/")
        self.assertNotContains(index, "dropdown-toggle active")
        self.assertContains(index, "nav-link active", count=1)

    def test_missing_tables_show_message_instead_of_error(self):
        empty = self.tmp / "empty.sqlite"
        pages = (("/db/lessons/", {}), ("/db/teachers/", {}),
                 ("/db/today/", {}), ("/db/stats/", {}),
                 ("/db/search/", {"teacher": "иванов"}))
        with override_settings(SQLITE_PATH=empty):
            for url, params in pages:
                with self.subTest(url=url):
                    response = self.client.get(url, params)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "python -m db.import_json")
