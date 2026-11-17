"""Сквозные тесты веб-интерфейса (запуск: python manage.py test).

Данные создаются через ORM во временной тестовой базе, которую Django
строит из миграций, поэтому тесты не зависят от настоящей базы. Часть
проверок относится к системе шаблонов (ПР6): наследование, include,
статика, статус 404.
"""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

import homepage.views
from lessons.factories import make_lesson
from lessons.models import Lesson
from rooms.models import Room
from teachers.models import Teacher


class SiteTests(TestCase):
    """Проверки страниц сайта на тестовых данных."""

    @classmethod
    def setUpTestData(cls):
        cls.math = make_lesson("Понедельник", "09:00", "Математика",
                               "Иванов И.И.", "301")
        cls.physics = make_lesson("Вторник", "10:00", "Физика",
                                  "Иванов И.И.", "302")
        cls.script = make_lesson("Среда", "11:00",
                                 "<script>alert(1)</script>",
                                 "Петров П.П.", "301")

    def test_index(self):
        response = self.client.get("/")
        self.assertContains(response, "Расписание занятий")
        self.assertContains(response, "bootstrap@5.3")
        self.assertContains(response, "Данные загружены")

    def test_index_with_empty_schedule(self):
        Lesson.objects.all().delete()
        self.assertContains(self.client.get("/"), "Расписание пусто")

    def test_lesson_list_and_detail(self):
        response = self.client.get("/lessons/")
        self.assertContains(response, "Математика")
        self.assertContains(
            response, f'href="/lessons/{self.physics.pk}/"')
        detail = self.client.get(f"/lessons/{self.math.pk}/")
        self.assertContains(detail, "Иванов И.И.")
        self.assertContains(
            detail, f'href="/teachers/{self.math.teacher_id}/"')
        self.assertContains(
            detail, f'href="/rooms/{self.math.room_id}/"')

    def test_lesson_detail_shows_time_and_day_status(self):
        # Вторник: не понедельник и не выходной, статус не зависит от даты.
        detail = self.client.get(f"/lessons/{self.physics.pk}/")
        self.assertContains(detail, "10:00")
        self.assertContains(detail, "Учебный день")

    def test_teacher_pages(self):
        self.assertContains(self.client.get("/teachers/"), "Петров П.П.")
        detail = self.client.get(f"/teachers/{self.math.teacher_id}/")
        self.assertContains(detail, "Математика")
        self.assertContains(detail, "Физика")
        self.assertNotContains(detail, "alert(1)")

    def test_room_pages(self):
        self.assertContains(self.client.get("/rooms/"), "ауд. 302")
        detail = self.client.get(f"/rooms/{self.math.room_id}/")
        self.assertContains(detail, "Математика")
        self.assertNotContains(detail, "Физика")

    def test_missing_objects_return_404(self):
        missing = Lesson.objects.order_by("-pk").first().pk + 1000
        for url in (f"/lessons/{missing}/", "/lessons/0/",
                    f"/teachers/{missing}/", f"/rooms/{missing}/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateUsed(response, "homepage/not_found.html")

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
        Lesson.objects.all().delete()
        make_lesson("Понедельник", "14:00", "Поздняя",
                    "Иванов И.И.", "301")
        make_lesson("Вторник", "09:00", "Вторничная",
                    "Иванов И.И.", "301")
        make_lesson("Понедельник", "09:00", "Ранняя",
                    "Иванов И.И.", "301")
        html = self.client.get("/lessons/").content.decode()
        self.assertLess(html.index("Ранняя"), html.index("Поздняя"))
        self.assertLess(html.index("Поздняя"), html.index("Вторничная"))

    def test_empty_schedule_has_no_day_groups(self):
        Lesson.objects.all().delete()
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
        room_url = reverse("rooms:detail", args=[self.math.room_id])
        self.assertContains(self.client.get(room_url),
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
        Lesson.objects.all().delete()
        Teacher.objects.all().delete()
        Room.objects.all().delete()
        self.assertContains(self.client.get("/lessons/"), "Расписание пусто")
        self.assertContains(self.client.get("/teachers/"),
                            "Преподавателей пока нет")
        self.assertContains(self.client.get("/rooms/"),
                            "Аудиторий пока нет")

    def test_404_handler_uses_template(self):
        response = self.client.get("/нет-такой-страницы/")
        self.assertTemplateUsed(response, "homepage/not_found.html")

    def test_page_helper_is_removed(self):
        self.assertFalse(hasattr(homepage.views, "page"))

    def test_pages_follow_changes_in_database(self):
        self.physics.delete()
        response = self.client.get("/lessons/")
        self.assertContains(response, "Всего занятий: 2")
        self.assertNotContains(response, "Физика")

    def test_empty_database_pages_do_not_fail(self):
        Lesson.objects.all().delete()
        for url in ("/", "/lessons/", "/teachers/", "/rooms/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_list_pages_use_constant_number_of_queries(self):
        # select_related() и annotate() не дают запросов на каждую строку.
        # Ещё один запрос — SELECT COUNT(*) контекстного процессора
        # room_context (ПР10), общий для всех страниц с base.html.
        with self.assertNumQueries(2):
            self.client.get("/lessons/")
        with self.assertNumQueries(2):
            self.client.get("/teachers/")
        with self.assertNumQueries(2):
            self.client.get("/rooms/")
        with self.assertNumQueries(2):
            self.client.get(f"/lessons/{self.math.pk}/")


class MediaTests(TestCase):
    """Раздача загруженных файлов и сообщения (ПР11)."""

    def test_missing_media_file_returns_404(self):
        response = self.client.get("/media/rooms/net-takogo.png")
        self.assertEqual(response.status_code, 404)

    def test_message_is_shown_once(self):
        lesson = make_lesson("Понедельник", "09:00", "Математика",
                             "Иванов И.И.", "301")
        first = self.client.post(f"/lessons/{lesson.pk}/cancel/",
                                 follow=True)
        self.assertContains(first, "alert-success")
        second = self.client.get("/lessons/")
        self.assertNotContains(second, "alert-success")
