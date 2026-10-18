"""Главная страница, общий HTML-каркас page() и страница ошибки 404."""

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from storage import load_schedule

BOOTSTRAP_CSS = ("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/"
                 "bootstrap.min.css")
BOOTSTRAP_JS = ("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/"
                "bootstrap.bundle.min.js")

# (имя маршрута, подпись) для навигации.
NAV_ITEMS = (
    ("homepage:index", "Главная"),
    ("lessons:list", "Занятия"),
    ("teachers:list", "Преподаватели"),
    ("rooms:list", "Аудитории"),
)


def page(title: str, content: str, status: int = 200) -> HttpResponse:
    """Собрать страницу в едином HTML-каркасе.

    title — заголовок вкладки (экранируется), content — готовый HTML
    основной части. Все данные из расписания перед вставкой в content
    нужно пропускать через escape().
    """
    links = "".join(
        f'<li class="nav-item"><a class="nav-link" '
        f'href="{reverse(name)}">{label}</a></li>'
        for name, label in NAV_ITEMS)
    index_url = reverse("homepage:index")
    html = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — Расписание занятий</title>
  <link href="{BOOTSTRAP_CSS}" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg bg-body-tertiary mb-4">
  <div class="container">
    <a class="navbar-brand" href="{index_url}">Расписание</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
            data-bs-target="#main-nav" aria-controls="main-nav"
            aria-expanded="false" aria-label="Меню">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="main-nav">
      <ul class="navbar-nav">{links}</ul>
    </div>
  </div>
</nav>
<main class="container pb-5">
{content}
</main>
<script src="{BOOTSTRAP_JS}"></script>
</body>
</html>"""
    return HttpResponse(html, status=status)


def not_found(message: str) -> HttpResponse:
    """Страница-сообщение со статусом 404 (для view и для handler404)."""
    content = f"""
<h1 class="display-4 text-danger">404</h1>
<p class="lead">{escape(message)}</p>
<a class="btn btn-primary" href="{reverse('homepage:index')}">На главную</a>
"""
    return page("Страница не найдена", content, status=404)


def page_not_found(request: HttpRequest,
                   exception: Exception) -> HttpResponse:
    """Обработчик 404 (подключён как handler404 в roomly/urls.py)."""
    return not_found("Такой страницы не существует.")


def index(request: HttpRequest) -> HttpResponse:
    """Главная: краткая сводка по расписанию и ссылки на разделы."""
    schedule = load_schedule()
    if schedule:
        status = '<span class="badge bg-success">Данные загружены</span>'
    else:
        status = '<span class="badge bg-danger">Расписание пусто</span>'
    sections = (
        ("Занятия", len(schedule), "lessons:list", "btn btn-primary"),
        ("Преподаватели", len(schedule.teachers), "teachers:list",
         "btn btn-secondary"),
        ("Аудитории", len(schedule.rooms), "rooms:list",
         "btn btn-outline-secondary"),
    )
    cards = "".join(f"""
  <div class="col-md-4">
    <div class="card h-100">
      <div class="card-body">
        <h2 class="card-title h5">{label}</h2>
        <p class="card-text">Всего: {count}</p>
        <a class="{css}" href="{reverse(route)}">Открыть</a>
      </div>
    </div>
  </div>""" for label, count, route, css in sections)
    content = f"""
<h1 class="display-4">Расписание занятий</h1>
<p>{status}</p>
<div class="row g-3">{cards}
</div>
"""
    return page("Главная", content)
