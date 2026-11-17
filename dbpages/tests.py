"""Тесты страниц раздела «Статистика и поиск» (запуск: manage.py test).

Данные создаются через ORM во временной тестовой базе: настоящие
db.sqlite3 и data/roomly.sqlite не затрагиваются.
"""

from datetime import datetime
from unittest.mock import patch

from django.test import TestCase

from lessons.factories import make_lesson
from lessons.models import Lesson
from teachers.models import Teacher

MONDAY_10 = datetime(2026, 10, 19, 10, 0)
SUNDAY_10 = datetime(2026, 10, 18, 10, 0)


class DbPagesTests(TestCase):
    """Страницы, получающие данные через Django ORM."""

    @classmethod
    def setUpTestData(cls):
        make_lesson("Понедельник", "09:00", "Математика",
                    "Иванов И.И.", "301")
        make_lesson("Понедельник", "11:00", "Физика",
                    "Иванов И.И.", "302")
        make_lesson("Понедельник", "13:00", "Химия",
                    "Петров П.П.", "303", lesson_type="лабораторная")
        make_lesson("Вторник", "10:00", "Алгебра",
                    "Петров П.П.", "301")
        make_lesson("Среда", "11:00", "<script>alert(1)</script>",
                    "Сидоров С.С.", "302")

    def test_lesson_list_uses_join_and_order(self):
        response = self.client.get("/db/lessons/")
        self.assertTemplateUsed(response, "dbpages/lesson_list.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "Иванов И.И.")
        self.assertContains(response, "лабораторная")
        html = response.content.decode()
        self.assertLess(html.index("Математика"), html.index("Алгебра"))
        self.assertLess(html.index("Математика"), html.index("Физика"))
        self.assertContains(response, "Найдено занятий: 5")

    def test_html_is_escaped(self):
        response = self.client.get("/db/lessons/", {"page": 2})
        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

    def test_lesson_list_is_one_page_of_five(self):
        response = self.client.get("/db/lessons/")
        self.assertEqual(len(response.context["lessons"]), 5)
        make_lesson("Четверг", "09:00", "История", "Сидоров С.С.", "301")
        first = self.client.get("/db/lessons/")
        self.assertEqual(len(first.context["lessons"]), 5)
        self.assertContains(first, 'aria-label="Навигация по страницам"')
        second = self.client.get("/db/lessons/", {"page": 2})
        self.assertEqual(len(second.context["lessons"]), 1)

    def test_pagination_is_hidden_for_one_page(self):
        response = self.client.get("/db/lessons/")
        self.assertNotContains(response, "pagination")

    def test_bad_page_number_opens_first_or_last_page(self):
        make_lesson("Четверг", "09:00", "История", "Сидоров С.С.", "301")
        for value, expected in (("abc", 1), ("", 1), ("999", 2)):
            with self.subTest(page=value):
                response = self.client.get("/db/lessons/", {"page": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["page_obj"].number,
                                 expected)

    def test_pagination_links_keep_filters_and_sort(self):
        for number in range(6):
            make_lesson("Пятница", f"1{number}:00", f"Предмет {number}",
                        "Иванов И.И.", f"5{number}0")
        response = self.client.get(
            "/db/lessons/",
            {"teacher": Lesson.objects.first().teacher_id,
             "sort": "subject"})
        self.assertContains(response, "sort=subject")
        self.assertContains(response, "page=2")

    def test_filter_by_day(self):
        response = self.client.get("/db/lessons/", {"day": "Вторник"})
        self.assertContains(response, "Алгебра")
        self.assertNotContains(response, "Математика")
        self.assertContains(response, "Найдено занятий: 1")

    def test_filter_by_teacher_and_room(self):
        petrov = Lesson.objects.get(subject__title="Алгебра")
        response = self.client.get(
            "/db/lessons/",
            {"teacher": petrov.teacher_id, "room": petrov.room_id})
        self.assertContains(response, "Алгебра")
        self.assertNotContains(response, "Химия")
        self.assertContains(response, "Найдено занятий: 1")

    def test_filter_by_subject_ignores_case(self):
        response = self.client.get("/db/lessons/", {"q": "ФИЗ"})
        self.assertContains(response, "Физика")
        self.assertNotContains(response, "Математика")

    def test_unknown_day_shows_error(self):
        response = self.client.get("/db/lessons/", {"day": "Foo"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Выберите день недели из списка.")
        self.assertContains(response, "Найдено занятий: 5")

    def test_garbage_ids_are_ignored(self):
        for value in ("abc", "-1", "1.5", "²", "9" * 30):
            with self.subTest(value=value):
                response = self.client.get(
                    "/db/lessons/", {"teacher": value, "room": value})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Найдено занятий: 5")

    def test_sort_by_subject_and_unknown_sort(self):
        by_subject = self.client.get("/db/lessons/", {"sort": "subject"})
        html = by_subject.content.decode()
        self.assertLess(html.index("Алгебра"), html.index("Математика"))
        self.assertLess(html.index("Математика"), html.index("Физика"))
        unknown = self.client.get("/db/lessons/",
                                  {"sort": "id; DROP TABLE x"})
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.context["sort"], "day")

    def test_teacher_list_orders_by_surname(self):
        response = self.client.get("/db/teachers/")
        html = response.content.decode()
        self.assertLess(html.index("Иванов И.И."), html.index("Петров"))
        self.assertLess(html.index("Петров"), html.index("Сидоров"))
        self.assertContains(response, "не указан", count=3)
        self.assertContains(response, "Математика, Физика")

    def test_teacher_list_uses_two_queries(self):
        # преподаватели + занятия с предметами (prefetch_related)
        with self.assertNumQueries(2):
            self.client.get("/db/teachers/")

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
        self.assertNotContains(response, "Иванов И.И.")

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

    def test_search_by_subject_or_room(self):
        by_subject = self.client.get("/db/search/", {"q": "матем"})
        self.assertContains(by_subject, "Математика")
        self.assertContains(by_subject, "Найдено занятий: 1")
        by_room = self.client.get("/db/search/", {"q": "301"})
        self.assertContains(by_room, "Математика")
        self.assertContains(by_room, "Алгебра")
        self.assertContains(by_room, "Найдено занятий: 2")

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

    def test_search_is_safe_against_special_characters(self):
        for value in ("' OR 1=1 --", "'; DROP TABLE lessons; --",
                      "%", "_", ".*", "(", "\\"):
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
        # не меньше двух занятий: аудитории 301 и 302, но не 303
        self.assertContains(response, "ауд. 301")
        self.assertContains(response, "ауд. 302")
        self.assertNotContains(response, "ауд. 303")
        self.assertContains(response, "Понедельник")

    def test_stats_summary_values(self):
        response = self.client.get("/db/stats/")
        summary = response.context["summary"]
        self.assertEqual(summary["lessons_count"], 5)
        self.assertEqual(summary["teachers_count"], 3)
        self.assertEqual(summary["rooms_count"], 3)
        self.assertEqual(summary["total_hours"], 7.5)

    def test_stats_by_teacher_counts_and_order(self):
        response = self.client.get("/db/stats/")
        rows = [(item.full_name, item.lessons_count)
                for item in response.context["by_teacher"]]
        self.assertEqual(rows, [("Иванов И.И.", 2), ("Петров П.П.", 2),
                                ("Сидоров С.С.", 1)])

    def test_stats_keep_teachers_and_rooms_without_lessons(self):
        Teacher.objects.create(full_name="Без Занятий Б.Б.")
        response = self.client.get("/db/stats/")
        names = [item.full_name for item in response.context["by_teacher"]]
        self.assertEqual(names[-1], "Без Занятий Б.Б.")
        last = list(response.context["by_teacher"])[-1]
        self.assertEqual(last.lessons_count, 0)
        self.assertContains(response, "Без Занятий Б.Б.")

    def test_stats_by_day(self):
        response = self.client.get("/db/stats/")
        by_day = response.context["by_day"]
        self.assertEqual([row["day_name"] for row in by_day],
                         ["Понедельник", "Вторник", "Среда"])
        self.assertEqual(by_day[0]["lessons_count"], 3)

    def test_pages_show_sql_query(self):
        for url in ("/db/lessons/", "/db/teachers/", "/db/stats/"):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), "SELECT")

    def test_navigation_links_use_url_names(self):
        response = self.client.get("/")
        for link in ("/db/stats/", "/db/today/", "/db/search/",
                     "/db/lessons/", "/rooms/free/"):
            self.assertContains(response, f'href="{link}"')
        self.assertContains(response, ">Статистика</button>")
        self.assertNotContains(response, ">База данных</button>")

    def test_navigation_marks_active_db_page(self):
        response = self.client.get("/db/stats/")
        self.assertContains(response, "dropdown-item active", count=1)
        self.assertContains(response, "dropdown-toggle active", count=1)
        index = self.client.get("/")
        self.assertNotContains(index, "dropdown-toggle active")
        self.assertContains(index, "nav-link active", count=1)

    def test_pages_work_with_empty_tables(self):
        Lesson.objects.all().delete()
        pages = ("/db/lessons/", "/db/teachers/", "/db/today/",
                 "/db/stats/", "/db/search/?teacher=иванов")
        for url in pages:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
