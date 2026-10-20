# Система расписания занятий

## Назначение

Приложение предназначено для хранения, просмотра и редактирования расписания учебных занятий.
Консольная версия приложения (ПР1–ПР3) дополнена веб-интерфейсом на Django (ПР5), страницы которого строятся с помощью системы шаблонов Django (ПР6).

Приложение позволяет:

* просматривать расписание занятий в браузере;
* просматривать информацию о конкретном занятии;
* просматривать список преподавателей и их занятия;
* просматривать список аудиторий и занятия в них;
* видеть, какие занятия проходят сегодня;
* добавлять и удалять занятия (консольная версия);
* искать занятия по названию предмета (консольная версия);
* показывать занятия на выбранный день и сортировать их по времени (консольная версия);
* хранить данные между запусками приложения.

## Используемые технологии

* Python 3.10+;
* Django 5.2 – веб-фреймворк;
* HTML и система шаблонов Django (наследование, `include`, фильтры) – разметка веб-страниц;
* CSS, JavaScript и Bootstrap 5.3 (подключён через CDN) – оформление страниц;
* статические файлы Django (`{% static %}`) – собственный CSS, JS и логотип;
* pytest – автоматизированные тесты;
* flake8 – проверка качества кода.

## Целевая аудитория

* Студенты, которые хотят вести личное расписание.
* Преподаватели для планирования своих занятий.
* Начинающие программисты как учебный пример консольного и веб-приложения на Python.

## Предметная область

Предметная область — учёт учебных занятий.

Основными объектами предметной области являются:

* занятие;
* преподаватель;
* аудитория;
* расписание.

Каждое занятие характеризуется днём недели, временем начала, названием предмета, преподавателем и аудиторией.
Расписание — это упорядоченный список таких занятий.

Правила предметной области:

* день недели — один из шести: Понедельник–Суббота;
* время задаётся в формате `ЧЧ:ММ` и нормализуется (`9:05` → `09:05`);
* название предмета, имя преподавателя и номер аудитории не могут быть пустыми;
* один и тот же преподаватель или аудитория — это один объект во всех занятиях расписания.

## Основные сущности

### Teacher – преподаватель

Объект `Teacher` представляет преподавателя, ведущего занятия.

Основные атрибуты:

* `name` – имя преподавателя (например, «Иванов И.И.»);
* `key` – ключ для JSON (совпадает с именем).

Основные методы:

* `surname` – фамилия (первое слово имени);
* `matches()` – проверка соответствия ключу;
* `__str__()` – строковое представление.

### Room – аудитория

Объект `Room` представляет аудиторию, в которой проходят занятия.

Основные атрибуты:

* `number` – номер аудитории (строка: «301», «12а»);
* `key` – ключ для JSON (совпадает с номером).

Основные методы:

* `matches()` – проверка соответствия ключу;
* `__str__()` – строковое представление («ауд. 301»).

`Teacher` и `Room` наследуют абстрактный класс `Entity`, который задаёт ключ, сравнение (`__eq__`), хеш и `__repr__`.

### Lesson – занятие

Объект `Lesson` представляет одно занятие.

Основные атрибуты:

* `day` – день недели (свойство с проверкой);
* `time` – время начала `ЧЧ:ММ` (свойство с проверкой и нормализацией);
* `subject` – название предмета (свойство с проверкой);
* `teacher` – объект `Teacher`;
* `room` – объект `Room`.

Основные методы:

* `parse_time()` – преобразование `ЧЧ:ММ` в минуты от начала суток;
* `start_minutes` – время начала в минутах (для сортировки);
* `matches_subject()` – поиск подстроки в названии предмета без учёта регистра;
* `is_on_day()` – проверка, проходит ли занятие в указанный день;
* `to_dict()` / `from_dict()` – преобразование в словарь JSON и обратно;
* `__str__()`, `__repr__()`, `__eq__()`.

### Schedule – расписание

Объект `Schedule` представляет коллекцию занятий и следит, чтобы одинаковые преподаватели и аудитории были одним объектом.

Основные методы:

* `add()`, `pop()` – добавление и удаление занятия;
* `lessons`, `teachers`, `rooms` – занятия, уникальные преподаватели и аудитории;
* `get_teacher()`, `get_room()` – вернуть известный объект или создать новый;
* `find_lesson_by_id()`, `find_teacher_by_id()`, `find_room_by_id()` – поиск по идентификатору (`None`, если не найден);
* `lesson_id()`, `teacher_id()`, `room_id()` – идентификатор объекта;
* `lessons_of_teacher()`, `lessons_in_room()` – занятия преподавателя и занятия в аудитории;
* `add_from_dict()`, `from_dicts()`, `to_dicts()` – преобразование из JSON и в JSON;
* `__len__()`, `__iter__()`, `__getitem__()`, `__str__()`.

Идентификатор в веб-интерфейсе — это порядковый номер объекта в списке, начиная с 1: для занятия – номер в расписании, для преподавателя и аудитории – номер в порядке первого появления. В JSON идентификаторы не хранятся и могут сдвинуться после удаления занятий.

## Страницы веб-интерфейса

* `/` – главная страница: сводка и навигация (view-функция `index()`);
* `/lessons/` – список занятий, сгруппированный по дням недели Понедельник–Суббота; внутри дня занятия идут по времени начала (view-функция `lesson_list()`);
* `/lessons/<int:lesson_id>/` – страница занятия (view-функция `lesson_detail()`);
* `/teachers/` – список преподавателей (view-функция `teacher_list()`);
* `/teachers/<int:teacher_id>/` – страница преподавателя и его занятия (view-функция `teacher_detail()`);
* `/rooms/` – список аудиторий (view-функция `room_list()`);
* `/rooms/<int:room_id>/` – страница аудитории и занятия в ней (view-функция `room_detail()`).

Если адрес не соответствует ни одному маршруту, обработчик `handler404` (`page_not_found()`) отображает шаблон `homepage/not_found.html` со статусом 404.
Если объект с указанным идентификатором не найден, view-функция передаёт в шаблон `None` и возвращает `render(..., status=404)`: шаблон страницы объекта через `{% if %}` показывает сообщение «не найден».

Все страницы наследуют общий шаблон `templates/base.html`; ссылки в них формируются тегом `{% url %}` по именам маршрутов (`homepage:index`, `lessons:list`, `lessons:detail`, `teachers:list`, `teachers:detail`, `rooms:list`, `rooms:detail`).

## Основные операции

### Используется в веб-интерфейсе (ПР5)

* просмотр списка занятий;
* просмотр информации о занятии (с проверкой статуса дня функцией `get_day_status()` из ПР1);
* выделение занятий, проходящих сегодня;
* просмотр списка преподавателей и аудиторий;
* просмотр занятий конкретного преподавателя и конкретной аудитории.

### Отложено до следующих работ

Эти операции реализованы в консольной версии (ПР1–ПР3). В веб-интерфейсе они появятся, когда будут добавлены формы и POST-запросы:

* добавление занятия;
* удаление занятия;
* поиск занятий по названию предмета;
* показ занятий на выбранный день;
* сортировка занятий по времени.

## Проектирование базы данных



| Сущность | Таблица | Поля | Типы | Ключи и ограничения |
|---|---|---|---|---|
| Преподаватель | `teachers` | `id`, `full_name`, `surname`, `email` | INTEGER, TEXT, TEXT, TEXT | PK `id`; `full_name` UNIQUE NOT NULL; `surname` NOT NULL; `email` может быть NULL |
| Аудитория | `rooms` | `id`, `number`, `floor`, `capacity` | INTEGER, TEXT, INTEGER, INTEGER | PK `id`; `number` UNIQUE NOT NULL; `floor` и `capacity` могут быть NULL; CHECK `capacity > 0` |
| Предмет | `subjects` | `id`, `title` | INTEGER, TEXT | PK `id`; `title` UNIQUE NOT NULL |
| Занятие | `lessons` | `id`, `day`, `day_number`, `start_time`, `duration_hours`, `lesson_type`, `subject_id`, `teacher_id`, `room_id` | INTEGER, TEXT, INTEGER, TEXT, REAL, TEXT, INTEGER, INTEGER, INTEGER | PK `id`; FK `subject_id` → `subjects.id`, `teacher_id` → `teachers.id`, `room_id` → `rooms.id` (ON DELETE RESTRICT, ON UPDATE CASCADE); `duration_hours` DEFAULT 1.5; `lesson_type` может быть NULL; CHECK на `day`, `day_number`, `start_time`; UNIQUE (`day_number`, `start_time`, `room_id`) и (`day_number`, `start_time`, `teacher_id`) |

## Создание базы и таблиц

Скрипт схемы — `sql/schema.sql` (`CREATE TABLE IF NOT EXISTS`, `NOT NULL`,
`DEFAULT`, `FOREIGN KEY`). Файл базы создаётся командой Python, а схема
выполняется через `executescript()` в функции `init_db()` модуля
`db/database.py`:

```text
python -m db.database
```

```text
База данных: .../data/roomly.sqlite
Таблицы: lessons, rooms, subjects, teachers
```

Проверка таблиц и внешних ключей (в SQLite CLI или через
`python -m db.check`):

```sql
SELECT name FROM sqlite_master WHERE type = 'table';
PRAGMA foreign_key_list(lessons);
```

Ожидается четыре таблицы и три внешних ключа: `rooms (room_id)`,
`teachers (teacher_id)`, `subjects (subject_id)`.

## Модули подключения и импорта

* `db/__init__.py` — пустой файл пакета;
* `db/database.py` — `get_connection()` (включает
  `PRAGMA foreign_keys = ON` и `sqlite3.Row`), `init_db()`;
* `db/import_json.py` — перенос `data/schedule.json` в таблицы:
  `executemany()` с параметрами `?` (без f-строк), одна транзакция,
  `try / except / finally` с `commit()` и `rollback()`;
* `db/check.py` — проверка структуры, количества записей, JOIN и запуск
  всех запросов из `sql/queries.sql`.

Запуск импорта из корня проекта:

```text
python -m db.import_json
```

## SQL-запросы (`sql/queries.sql`)

В файле 21 запрос; у каждого есть комментарий `--` с назначением и
ожидаемым результатом. Заголовок вида `-- Запрос N [ТЕГИ].` позволяет
`db/check.py` и тестам разбирать файл.

| Вид | Запросы |
|---|---|
| Выборка списков (`SELECT` + `ORDER BY`) | 1, 2, 3, 12 |
| Фильтрация (`WHERE`, `AND/OR/NOT`, `BETWEEN`, `IN`, `LIKE`, `IS NULL`) | 4–9 (и 21) |
| Соединение таблиц (`JOIN` 2, 3 и 4 таблиц) | 10, 11, 12 (и 16, 18–20) |
| Агрегатные функции (`COUNT`, `MIN`, `MAX`, `AVG`, `SUM`) | 13, 14, 15 (и 16, 17) |
| Группировка (`GROUP BY`, `HAVING`) | 16, 17, 18, 19, 20 |
| `LIMIT` / `OFFSET`, подзапросы (`NOT IN`, подзапрос в `HAVING`) | 3, 20, 21 |

Проверка в SQLite CLI, из корня проекта:

```text
sqlite3 data/roomly.sqlite
sqlite> .headers on
sqlite> .mode column
sqlite> .read sql/queries.sql
```


## Структура проекта

```text
lesson_schedule/
│
├── README.md
├── requirements.txt
├── manage.py
├── main.py
├── schedule.py
├── storage.py
├── utils.py
├── conftest.py
├── .flake8
│
├── roomly/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── templates/
│   ├── base.html
│   └── includes/
│       └── navigation.html
│
├── homepage/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── static/homepage/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── img/logo.png
│   └── templates/homepage/
│       ├── index.html
│       ├── not_found.html
│       └── includes/section_card.html
│
├── lessons/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── presenters.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── templates/lessons/
│       ├── lesson_list.html
│       ├── lesson_detail.html
│       └── includes/
│           ├── lesson_card.html
│           └── lesson_status.html
│
├── teachers/
│   ├── (те же .py-файлы, что в lessons/, включая presenters.py)
│   └── templates/teachers/
│       ├── teacher_list.html
│       ├── teacher_detail.html
│       └── includes/
│           ├── teacher_card.html
│           └── teacher_status.html
│
├── rooms/
│   ├── (те же .py-файлы, что в lessons/, включая presenters.py)
│   └── templates/rooms/
│       ├── room_list.html
│       ├── room_detail.html
│       └── includes/
│           ├── room_card.html
│           └── room_status.html
│
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── teacher.py
│   ├── room.py
│   ├── lesson.py
│   └── schedule.py
│
├── data/
│   └── schedule.json
│
└── tests/
    ├── test_teacher_room.py
    ├── test_lesson.py
    ├── test_schedule_model.py
    ├── test_schedule.py
    ├── test_storage.py
    └── test_main.py
```




## Назначение модулей

### `main.py`

Консольная версия приложения (сохранена с ПР1–ПР3).

Отвечает за:

* запуск консольного приложения;
* отображение меню;
* получение данных от пользователя;
* организацию пользовательских сценариев.

### `roomly/`

Пакет настроек Django-проекта:

* `settings.py` – настройки проекта (приложения, язык `ru-RU`, часовой пояс `Europe/Moscow`, `DEBUG`, `ALLOWED_HOSTS`);
* `urls.py` – маршрутизация верхнего уровня и обработчик `handler404`;
* `asgi.py`, `wsgi.py` – точки взаимодействия с сервером.

### `homepage/`

Django-приложение, отвечающее за главную страницу:

* `views.py` – view-функция `index()` и обработчик 404 `page_not_found()`; HTML в файле больше нет, обе функции вызывают `render()`;
* `urls.py` – маршрут главной страницы;
* `templates/homepage/` – шаблоны главной страницы и страницы 404, включаемый шаблон карточки раздела;
* `static/homepage/` – общие статические файлы проекта: `css/style.css`, `js/main.js`, `img/logo.png`.

Функция `page()` из ПР5 удалена: общий каркас страниц теперь находится в `templates/base.html`.

### `lessons/`

Django-приложение, отвечающее за занятия:

* `views.py` – view-функции `lesson_list()` и `lesson_detail()`;
* `presenters.py` – подготовка данных для шаблонов (без HTML): `LessonItem`, `DayGroup`, `build_lesson_items()`, `build_day_groups()` (группировка по дням с помощью `filter_lessons_by_day()` и `sort_lessons_by_time()` из ПР3), `today_name()`; используется также в `homepage`, `teachers` и `rooms`;
* `templates/lessons/` – шаблоны списка и страницы занятия, включаемые шаблоны `lesson_card.html` (карточка) и `lesson_status.html` (бейдж дня, подключается в списках, на страницах занятия, преподавателя и аудитории);
* `urls.py` – маршруты приложения;
* `models.py` – Django-модели (заполняется в следующих работах).

### `teachers/`

Django-приложение, отвечающее за преподавателей:

* `views.py` – view-функции `teacher_list()` и `teacher_detail()`;
* `presenters.py` – `TeacherItem` и функции его построения;
* `templates/teachers/` – шаблоны списка и страницы преподавателя, включаемые шаблоны `teacher_card.html` (карточка) и `teacher_status.html`;
* `urls.py` – маршруты приложения;
* `models.py` – Django-модели (заполняется в следующих работах).

### `rooms/`

Django-приложение, отвечающее за аудитории:

* `views.py` – view-функции `room_list()` и `room_detail()`;
* `presenters.py` – `RoomItem` и функции его построения;
* `templates/rooms/` – шаблоны списка и страницы аудитории, включаемые шаблоны `room_card.html` (карточка) и `room_status.html`;
* `urls.py` – маршруты приложения;
* `models.py` – Django-модели (заполняется в следующих работах).

Отдельное приложение для пользователей не создавалось: в проекте нет пользователей, а для будущей авторизации Django предоставляет встроенную модель `User` из `django.contrib.auth`.

### `templates/` и шаблоны приложений

* `templates/base.html` – базовый шаблон: `DOCTYPE`, Bootstrap 5.3, собственный CSS, шапка с логотипом, подключение навигации, блоки `title` и `content`, подвал, скрипты;
* `templates/includes/navigation.html` – меню; ссылки формируются через `{% url %}`, активный раздел определяется по пространству имён (`request.resolver_match.namespace`);
* шаблоны страниц наследуют `base.html` через `{% extends %}` и переопределяют блоки;
* для коллекций используются `{% for %}` с `{% empty %}`, для состояний – `{% if %}`;
* фильтры (`length`, `default`, `truncatechars`, `upper`, `date`) отвечают только за форматирование вывода, а не за бизнес-логику: данные готовятся во view и `presenters.py`.

Каталог шаблонов проекта подключён в `settings.py`: `TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`; шаблоны приложений находятся автоматически (`APP_DIRS = True`).

### `models/`

Классы предметной области (пакет ПР3):

* `base.py` – абстрактный класс `Entity`;
* `teacher.py` – класс `Teacher`;
* `room.py` – класс `Room`;
* `lesson.py` – класс `Lesson` и список дней недели `DAYS`;
* `schedule.py` – класс `Schedule`.

Не следует путать пакет `models/` (обычные классы Python) и файлы `models.py` в Django-приложениях (ORM-модели Django).

### `schedule.py`

Функции работы с коллекциями занятий: `add_lesson()`, `find_lessons()`, `filter_lessons_by_day()`, `sort_lessons_by_time()`, `delete_lesson()`, `get_day_status()`.

### `storage.py`

Отвечает за загрузку и сохранение данных (`load_schedule()`, `save_schedule()`).

Выполняет преобразование:

* JSON → объекты Python;
* объекты Python → JSON.

### `utils.py`

Содержит вспомогательные функции консольного ввода:

* `input_int()` – безопасный ввод целого числа;
* `input_nonempty()` – ввод непустой строки;
* `input_date()` – безопасный ввод даты.

### `tests/`

Содержит автоматизированные тесты проекта. Тесты веб-интерфейса находятся в `homepage/tests.py`.

## Запуск приложения

Команды выполняются из корня проекта: файл `data/schedule.json` ищется относительно текущей папки.

Веб-версия (Django):

```text
python manage.py runserver
```

После запуска открыть в браузере адрес:

```text
http://127.0.0.1:8000/
```

Консольная версия (сохранена):

```text
python main.py
```

В `settings.py` по умолчанию `DEBUG = False` (так видна своя страница 404) и `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]`. При `DEBUG = False` Django сам не отдаёт статические файлы, поэтому в `roomly/urls.py` добавлен маршрут `static/<path:path>` (`django.contrib.staticfiles.views.serve` с `insecure=True`). Благодаря ему CSS, JavaScript и логотип загружаются при обычном `python manage.py runserver`. Для реального развёртывания статику должен отдавать веб-сервер после `collectstatic`.

Отладку можно включить переменной окружения `ROOMLY_DEBUG=1` (тогда вместо своей страницы 404 для неизвестных адресов Django показывает отладочную).

Проверка подключения статики:

```text
python manage.py findstatic homepage/img/logo.png
```

## Тестирование

Для запуска автоматизированных тестов выполнить:

```text
pytest -v
python manage.py test
```

Первая команда запускает тесты предметной области, хранилища и консольного меню из `tests/`, вторая – тесты веб-интерфейса.

## Проверка качества кода

Для проверки соответствия кода требованиям PEP 8 используется `flake8`.

Команда проверки:

```text
flake8 .
```

## Зависимости

Состав зависимостей в `requirements.txt`:

* `Django>=5.2,<6.0` – веб-фреймворк;
* `pytest>=8.0` – автоматизированные тесты;
* `flake8>=7.0` – проверка качества кода.

Установка:

```text
pip install -r requirements.txt
```

## Git

Исходный код проекта хранится в Git-репозитории.

Для проверки состояния репозитория:

```text
git status
```

## Запуск и проверка

```text
python -m db.import_json          # создать базу и загрузить данные
python -m db.check --queries      # проверить таблицы, данные и запросы
python manage.py runserver        # открыть http://127.0.0.1:8000/db/stats/
pytest -v                         # тесты ПР1–ПР3 и tests/test_db.py
python manage.py test             # тесты сайта и dbpages/tests.py
flake8 .
```

## Текущее состояние и план развития



Реализовано (ПР6):

* система шаблонов Django: базовый шаблон `base.html`, наследование (`{% extends %}`, `{% block %}`), включаемые шаблоны (`{% include %}`);
* передача данных во view через контекст, `render()`, цикл `{% for %}` с `{% empty %}`, условия `{% if %}`;
* ссылки через `{% url %}` с пространствами имён, фильтры шаблонов;
* статические файлы: собственный CSS, JavaScript, логотип;
* функция `page()` и HTML-строки в `views.py` удалены;
* статус 404 для несуществующих объектов задаётся в `render(..., status=404)`.

Реализовано (ПР5):

* Django-проект и четыре Django-приложения (`homepage`, `lessons`, `teachers`, `rooms`);
* маршрутизация URL двух уровней;
* view-функции и страницы просмотра;
* отображение данных предметной области (занятия, преподаватели, аудитории);
* использование объектной модели ПР3 и функции `get_day_status()` из ПР1;
* страница 404 (`handler404`);
* навигация между страницами;
* оформление Bootstrap 5.3.

Планируется:

* перенос сущностей `Lesson`, `Teacher` и `Room` в Django ORM и подключение базы данных (SQLite) вместо JSON;
* формы добавления и удаления занятий;
* использование отложенной логики ПР3 (`add_lesson()`, `delete_lesson()`, поиск, фильтрация по дню, сортировка);
* фильтрация по преподавателю;
* редактирование существующих записей;
* экспорт расписания в CSV/ICS;
* учёт чётности недели (числитель/знаменатель);
* CI.
