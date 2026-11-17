# Система расписания занятий

## Назначение

Приложение предназначено для хранения, просмотра и редактирования расписания учебных занятий.
Консольная версия приложения (ПР1–ПР3) дополнена веб-интерфейсом на Django (ПР5), страницы которого строятся с помощью системы шаблонов Django (ПР6). Данные хранятся в SQLite (ПР7), с ПР9 страницы получают их через Django ORM, с ПР10 данными можно управлять через административную панель Django (`/admin/`), а с ПР11 занятия и аудитории создаются и редактируются через формы Django.

Приложение позволяет:

* просматривать расписание занятий в браузере;
* просматривать информацию о конкретном занятии;
* просматривать список преподавателей и их занятия;
* просматривать список аудиторий и занятия в них;
* видеть, какие занятия проходят сегодня;
* добавлять, редактировать и отменять занятия в браузере (ПР11), добавлять аудитории с фотографией;
* добавлять и удалять занятия (консольная версия);
* искать занятия по названию предмета (консольная версия);
* показывать занятия на выбранный день и сортировать их по времени (консольная версия);
* хранить данные между запусками приложения.

## Используемые технологии

* Python 3.10+;
* Django 5.2 – веб-фреймворк;
* SQLite и Django ORM (модели, миграции, QuerySet) – хранение и получение данных;
* HTML и система шаблонов Django (наследование, `include`, фильтры) – разметка веб-страниц;
* CSS, JavaScript и Bootstrap 5.3 (подключён через CDN) – оформление страниц;
* статические файлы Django (`{% static %}`) – собственный CSS, JS и логотип;
* Django Forms (`Form`, `ModelForm`) и Pillow (`ImageField`) – формы и загрузка изображений (ПР11);
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
* `/rooms/<int:room_id>/` – страница аудитории и занятия в ней (view-функция `room_detail()`);
* `/rooms/<slug:slug>/` – та же страница по slug, например `/rooms/auditoriya-301-1/` (ПР10, `room_detail_by_slug()`, имя маршрута `rooms:slug_detail`);
* `/admin/` – административная панель Django (ПР10);
* `/lessons/create/`, `/lessons/<int:lesson_id>/edit/`, `/lessons/<int:lesson_id>/cancel/` – создание, редактирование и отмена занятия (ПР11, `lessons:create`, `lessons:update`, `lessons:cancel`; отмена принимает только POST);
* `/rooms/create/`, `/rooms/<int:room_id>/edit/` – создание и редактирование аудитории с изображением (ПР11, `rooms:create`, `rooms:update`);
* `/media/<путь>` – загруженные изображения (ПР11, в разработке их отдаёт сам Django).
* `/rooms/free/` – поиск свободных аудиторий на выбранные день и время (`free_rooms()`);
* `/db/lessons/`, `/db/teachers/`, `/db/today/`, `/db/search/`, `/db/stats/` – страницы на ORM: фильтры, сортировка, пагинация, поиск, статистика (приложение `dbpages`).

Если адрес не соответствует ни одному маршруту, обработчик `handler404` (`page_not_found()`) отображает шаблон `homepage/not_found.html` со статусом 404.
Если объект с указанным идентификатором не найден, `get_object_or_404()` прекращает обработку запроса, и Django возвращает ответ 404 со страницей `homepage/not_found.html`.

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


## Django ORM (ПР9)

В ПР9 слой данных переведён с `sqlite3` и ручных SQL-запросов на Django ORM. Страницы, шаблоны, имена маршрутов и пользовательские сценарии сохранены; изменился только способ получения данных. Цепочка: представление → Django ORM → SQLite → объекты моделей.

### Модели

Проект «Система расписания занятий» не содержит сущностей User и Booking, поэтому модели построены по таблицам ПР7 (`teachers`, `rooms`, `subjects`, `lessons`):

| Модель | Приложение | Поля | Связи и ограничения |
|---|---|---|---|
| `TimeStampedModel` (абстрактная) | `homepage` | `created_at` (`auto_now_add`), `updated_at` (`auto_now`) | таблицы не создаёт; поля наследуют все модели ниже |
| `Teacher` | `teachers` | `full_name`, `surname`, `email` | `full_name` уникально; `email` необязателен (`blank=True`, `default=""`); `surname` заполняется в `save()` из `full_name`; сортировка по фамилии |
| `Room` | `rooms` | `number`, `floor`, `capacity` | `number` уникален; `floor` и `capacity` необязательны (`null=True`, `blank=True`); `CheckConstraint`: вместимость пуста или больше 0 |
| `Subject` | `lessons` | `title` | `title` уникально |
| `Lesson` | `lessons` | `day` (число 1–6 с подписями), `start_time` (`TimeField`), `duration_hours` (по умолчанию 1.5), `lesson_type`, `subject`, `teacher`, `room` | три `ForeignKey` с `on_delete=PROTECT` и `related_name="lessons"`; `UniqueConstraint` (`day`, `start_time`, `room`) и (`day`, `start_time`, `teacher`); `CheckConstraint` на день и длительность |

Обратный доступ: `teacher.lessons.all()`, `room.lessons.all()`, `subject.lessons.all()`. `PROTECT` запрещает удалять преподавателя, аудиторию или предмет, пока на них ссылаются занятия, – так же работал `ON DELETE RESTRICT` в ПР7. День недели хранится числом (удобно сортировать), название даёт `lesson.get_day_display()`. Не путать модели `models.py` Django-приложений с обычными классами пакета `models/` (ПР3).

### Миграции и перенос данных

Стратегия – вариант 2 из методических указаний: Django создаёт собственные таблицы в `db.sqlite3`, а исходная база ПР7 `data/roomly.sqlite` остаётся без изменений и служит источником данных.

```text
python manage.py migrate                 # создать таблицы (миграции 0001_initial в teachers, rooms, lessons)
python -m db.inspect_source_db           # посмотреть структуру исходной базы (только чтение)
python -m db.import_sqlite_to_orm        # перенести данные через ORM
python manage.py makemigrations --check  # модели и миграции согласованы
```

Скрипт переноса сохраняет первичные ключи и связи, преобразует время `«ЧЧ:ММ»` в `time`, `NULL` текстовых полей в пустую строку, выполняется одной транзакцией (`transaction.atomic()`) и безопасен при повторном запуске (`update_or_create()`). Файл `db.sqlite3` исключён из Git (`.gitignore`): после клонирования таблицы создаются миграциями, данные – скриптом переноса.

### ORM-запросы в проекте

| Вид | Выражение | Где |
|---|---|---|
| Получение набора | `Lesson.objects.all()`, `.order_by()` | `dbpages/views.py`, `lessons/views.py` |
| Получение одного объекта | `get_object_or_404(..., pk=...)` | `lessons`, `teachers`, `rooms` (страницы объектов) |
| Фильтрация по одному условию | `filter(day=...)`, `filter(teacher_id=...)` | `dbpages.lesson_list`, `search_lessons` |
| Фильтрация по нескольким условиям | цепочка `filter()` по дню, преподавателю, аудитории, предмету | `dbpages.lesson_list` |
| Фильтрация по полю связанной модели | `subject__title`, `teacher__full_name`, `room__number` | `dbpages/views.py` |
| Исключение | `Room.objects.exclude(pk__in=...)` | `rooms.free_rooms` |
| Поиск по строке | `contains_nocase()` (`iregex`, без учёта регистра кириллицы) | `dbpages.search_lessons` |
| Поиск по нескольким полям | `Q(...) \| Q(...)` – предмет или аудитория | `dbpages.search_lessons` |
| Сортировка | `order_by("day", "start_time", "pk")`; поле связанной модели `teacher__surname` | `lessons`, `dbpages.lesson_list` |
| Выбор поля сортировки | словарь `SORT_FIELDS`, неизвестное значение → `day` | `dbpages.lesson_list` |
| Связанные объекты | `select_related("subject", "teacher", "room")` | `lessons`, `homepage`, `teachers`, `rooms` |
| Связанные объекты | `prefetch_related(Prefetch(...))`, обратная связь `teacher.lessons` | `dbpages.teacher_list`, `teacher_detail` |
| Сокращённый набор полей | `values()`, `values_list("room_id", flat=True)` | `dbpages/views.py`, `rooms.free_rooms` |
| Вычисляемые поля | `annotate(F("subject__title"), Case/When)` | `dbpages.lesson_rows` |
| Сводный показатель | `aggregate(Count, Sum, Min, Max)` | `dbpages.stats` |
| Показатель по объектам | `annotate(Count("lessons"), Sum(...))`, `Count(..., filter=Q(...))` | `dbpages.stats`, `teachers`, `rooms` |
| Группировка | `values("day").annotate(Count("id"))` | `dbpages.stats` |
| Фильтр по аннотации (HAVING) | `annotate(...).filter(lessons_count__gte=2)` | `dbpages.stats` |
| Подсчёт и проверка | `count()`, `exists()` | `homepage.index` |
| Постраничный вывод | `Paginator(rows, 5)`, `get_page()`, `{% querystring page=... %}` | `dbpages.lesson_list` |

Статистика строится от моделей `Teacher` и `Room`, поэтому преподаватели и аудитории без занятий не пропадают из результата (счётчик равен 0), – аналог `LEFT JOIN` из ПР7. Если страница не найдена, `get_object_or_404()` возвращает ответ 404 (шаблон `homepage/not_found.html`); некорректные параметры (`day`, `time`, `page`, числовые идентификаторы) не приводят к ошибке.

Регистр кириллицы: `LIKE` в SQLite (и `icontains`) не различает регистр только у латиницы, поэтому для поиска по тексту используется `iregex` с `re.escape()`: Django выполняет REGEXP средствами Python.

Работа через Django shell (`python manage.py shell`):

```python
from lessons.models import Lesson
from rooms.models import Room

room = Room.objects.create(number="500", floor=5, capacity=40)   # Create
Room.objects.filter(capacity__gte=30)                            # Read
room.capacity = 45
room.save()                                                      # Update
room.delete()                                                    # Delete
lesson = Lesson.objects.select_related("room", "teacher").first()
lesson.room.number, lesson.teacher.full_name                     # прямая связь
lesson.teacher.lessons.count()                                   # обратная связь
```

Прежний слой `sqlite3` (`db/database.py`, `db/import_json.py`, `db/repository.py`, `db/check.py`, `sql/schema.sql`, `sql/queries.sql`) сохранён как реализация ПР7: страницы сайта его больше не используют.

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
│   ├── models.py              (абстрактная TimeStampedModel)
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
│   ├── forms.py               (ПР11: LessonForm)
│   ├── models.py              (Subject, Lesson)
│   ├── factories.py           (тестовые данные через ORM)
│   ├── presenters.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/0001_initial.py
│   └── templates/lessons/
│       ├── lesson_list.html
│       ├── lesson_detail.html
│       └── includes/
│           ├── lesson_card.html
│           └── lesson_status.html
│
├── teachers/
│   ├── (те же .py-файлы, что в lessons/; models.py – Teacher)
│   ├── migrations/0001_initial.py
│   └── templates/teachers/
│       ├── teacher_list.html
│       ├── teacher_detail.html
│       └── includes/
│           ├── teacher_card.html
│           └── teacher_status.html
│
├── rooms/
│   ├── (те же .py-файлы, что в lessons/; models.py – Room)
│   ├── slugs.py               (ПР10: slug аудитории)
│   ├── forms.py               (ПР11: RoomForm с изображением)
│   ├── context_processors.py  (ПР10: room_context)
│   ├── migrations/            (0001–0005: таблица, slug, is_large)
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
├── dbpages/                   (страницы статистики и поиска на ORM; forms.py – LessonFilterForm, ПР11)
│
├── db/
│   ├── inspect_source_db.py   (ПР9: структура исходной базы)
│   ├── import_sqlite_to_orm.py (ПР9: перенос данных в базу Django)
│   └── (слой sqlite3 ПР7: database.py, import_json.py, repository.py, check.py)
│
├── sql/                       (schema.sql, queries.sql – ПР7)
│
├── data/
│   ├── schedule.json
│   └── roomly.sqlite          (исходная база ПР7)
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

* `views.py` – view-функции `lesson_list()` и `lesson_detail()`: запросы выполняются через ORM (`select_related()`, `get_object_or_404()`);
* `presenters.py` – превращает объекты `Lesson` в элементы для шаблонов (без HTML и без обращений к базе): `LessonItem`, `DayGroup`, `build_lesson_items()`, `build_day_groups()`, `today_name()`, `today_number()`; используется также в `homepage`, `teachers` и `rooms`;
* `templates/lessons/` – шаблоны списка и страницы занятия, включаемые шаблоны `lesson_card.html` (карточка) и `lesson_status.html` (бейдж дня, подключается в списках, на страницах занятия, преподавателя и аудитории);
* `urls.py` – маршруты приложения;
* `models.py` – Django-модели `Subject` и `Lesson` (ПР9), `migrations/` – миграции;
* `factories.py` – создание тестовых данных через ORM.

### `teachers/`

Django-приложение, отвечающее за преподавателей:

* `views.py` – view-функции `teacher_list()` и `teacher_detail()`;
* `presenters.py` – `TeacherItem` и функции его построения;
* `templates/teachers/` – шаблоны списка и страницы преподавателя, включаемые шаблоны `teacher_card.html` (карточка) и `teacher_status.html`;
* `urls.py` – маршруты приложения;
* `models.py` – Django-модель `Teacher` (ПР9), `migrations/` – миграции.

### `rooms/`

Django-приложение, отвечающее за аудитории:

* `views.py` – view-функции `room_list()` и `room_detail()`;
* `presenters.py` – `RoomItem` и функции его построения;
* `templates/rooms/` – шаблоны списка и страницы аудитории, включаемые шаблоны `room_card.html` (карточка) и `room_status.html`;
* `urls.py` – маршруты приложения;
* `models.py` – Django-модель `Room` (ПР9; ПР10: `slug`, `get_absolute_url()`, `GeneratedField` `is_large`), `migrations/` – миграции;
* `slugs.py` – транслитерация и построение slug (ПР10);
* `context_processors.py` – контекстный процессор `room_context` (ПР10);
* `admin.py` – `RoomAdmin` и inline занятий (ПР10);
* страница `/rooms/free/` – поиск свободных аудиторий.

Отдельное приложение для пользователей не создавалось: в проекте нет пользователей, а для будущей авторизации Django предоставляет встроенную модель `User` из `django.contrib.auth`.

### `templates/` и шаблоны приложений

* `templates/base.html` – базовый шаблон: `DOCTYPE`, Bootstrap 5.3, собственный CSS, шапка с логотипом, подключение навигации, блоки `title` и `content`, подвал, скрипты;
* `templates/includes/navigation.html` – меню; ссылки формируются через `{% url %}`, активный раздел определяется по пространству имён (`request.resolver_match.namespace`);
* шаблоны страниц наследуют `base.html` через `{% extends %}` и переопределяют блоки;
* для коллекций используются `{% for %}` с `{% empty %}`, для состояний – `{% if %}`;
* фильтры (`length`, `default`, `truncatechars`, `upper`, `date`) отвечают только за форматирование вывода, а не за бизнес-логику: данные готовятся во view и `presenters.py`.

Каталог шаблонов проекта подключён в `settings.py`: `TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`; шаблоны приложений находятся автоматически (`APP_DIRS = True`).

### `dbpages/`

Страницы раздела «Статистика» (`/db/...`), построенные на ORM: `lesson_list()` (фильтры, сортировка, пагинация), `teacher_list()`, `today_lessons()`, `search_lessons()`, `stats()`. Под таблицами показан SQL, который построил Django.

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

Веб-версия (Django). При первом запуске создайте таблицы и перенесите данные:

```text
python manage.py migrate
python -m db.import_sqlite_to_orm
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

Первая команда запускает тесты предметной области, хранилища, консольного меню и слоя sqlite3 (ПР7) из `tests/`, вторая – тесты веб-интерфейса, моделей Django, переноса данных и страниц на ORM (используют временную тестовую базу).

## Проверка качества кода

Для проверки соответствия кода требованиям PEP 8 используется `flake8`.

Команда проверки:

```text
flake8 .
```

## Зависимости

Состав зависимостей в `requirements.txt`:

* `Django>=5.2,<6.0` – веб-фреймворк;
* `Pillow>=10.0` – нужна для `ImageField` (ПР11);
* `pytest>=8.0` – автоматизированные тесты;
* `flake8>=7.0` – проверка качества кода;
* `django-debug-toolbar>=4.4` – панель анализа SQL-запросов (ПР10, необязательна: без неё сайт и тесты работают).

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
python manage.py migrate                 # создать таблицы Django
python -m db.import_sqlite_to_orm        # перенести данные из data/roomly.sqlite
python manage.py check                   # проверка конфигурации и моделей
python manage.py showmigrations          # миграции применены ([X])
python manage.py makemigrations --check  # нет неописанных изменений моделей
python manage.py runserver               # http://127.0.0.1:8000/
pytest -v                                # тесты ПР1–ПР3 и слоя sqlite3 (ПР7)
python manage.py test                    # тесты сайта, моделей и ORM-страниц
flake8 . --extend-exclude=venv
```

## Административная панель и ORM (ПР10)

Предметная область проекта – расписание, поэтому сущности методички (помещение, пользователь, бронирование) соответствуют так: `Room` → аудитория (`rooms.Room`), «пользователь» → преподаватель (`teachers.Teacher`), `Booking` → занятие (`lessons.Lesson`; предмет вынесен в справочник `lessons.Subject`). Статусы бронирований заменены типом занятия (`Lesson.LessonType`), «активное бронирование» – занятие в расписании.

### Django Admin (`/admin/`)

Суперпользователь создаётся командой `python manage.py createsuperuser` (учётная запись Django, не преподаватель предметной области).

| Модель | Настройки `ModelAdmin` |
| --- | --- |
| `Room` | `list_display` (номер, этаж, вместимость, большая, число занятий, slug), `list_display_links`, `list_editable` (вместимость прямо в списке), `list_filter` (этаж, большая), `search_fields`, `ordering`, `list_per_page`, `readonly_fields` (`is_large`, `slug`, даты), inline занятий аудитории, ссылка «Смотреть на сайте» через `get_absolute_url()` |
| `Teacher` | список с числом занятий (`annotate(Count)` + `admin.display`), поиск по ФИО, фамилии и почте, inline занятий преподавателя |
| `Subject` | список с числом занятий, поиск по названию |
| `Lesson` | `list_filter` (день, тип, аудитория, преподаватель), поиск по полям связанных моделей (`subject__title`, `teacher__full_name`, `room__number`), `list_select_related`, `autocomplete_fields`, массовые действия «Отметить как лабораторные» и «Сбросить тип» |

Названия приложений заданы `verbose_name` в `AppConfig`, моделей и полей – в `verbose_name` моделей, язык интерфейса – `LANGUAGE_CODE = "ru-RU"`; заголовки панели – в `homepage/admin.py`.

Админка не заменяет бизнес-правила: конфликт «аудитория/преподаватель + день + время» запрещён ограничениями `UniqueConstraint` модели `Lesson`, поэтому форма админки покажет ошибку, а не сохранит дубликат.

### Изменения моделей и миграции

* `Room.slug` (`SlugField`, уникальный, создаётся в `save()` как `auditoriya-<номер латиницей>-<pk>`) и `Room.get_absolute_url()`; миграции `rooms/0002` (поле), `0003` (заполнение slug у существующих аудиторий), `0004` (уникальность);
* `Room.is_large` – `GeneratedField`: база сама вычисляет признак «вместимость ≥ 50» (`db_persist=True`), миграция `rooms/0005`;
* `Lesson.LessonType` (`TextChoices`: лабораторная, лекция, практика) – миграция `lessons/0002` меняет только список допустимых значений, существующие записи не преобразуются, так как в базе остаются те же строки;
* `LessonQuerySet` / менеджер `Lesson.objects`: `on_day()`, `for_teacher()`, `for_room()`, `at()`, `laboratory()`, `regular()`, `with_related()` – используются в представлениях вместо повторяющихся `filter()`/`select_related()`.

### Контекстный процессор

`rooms.context_processors.room_context` добавляет во все шаблоны `site_name` и `rooms_total` (выводятся в подвале `base.html`), зарегистрирован в `TEMPLATES` в `settings.py`. Он выполняет один `SELECT COUNT(*)` на страницу.

### Django Debug Toolbar

Панель подключается в `settings.py` только при `ROOMLY_DEBUG=1` и если пакет установлен:

```text
pip install django-debug-toolbar
set ROOMLY_DEBUG=1          (PowerShell: $env:ROOMLY_DEBUG = "1")
python manage.py runserver
```

На страницах появляется панель с вкладкой SQL (маршруты `__debug__/` подключаются в `roomly/urls.py`). Ожидаемое число запросов: списки занятий, преподавателей и аудиторий – 1 запрос данных + 1 запрос `COUNT(*)` процессора; `/db/lessons/` – запрос `COUNT(*)` пагинатора + запрос текущей страницы (связанные поля берутся одним запросом через `annotate(F(...))` + `values()`, `select_related()` не нужен).

### Проверка

```text
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
pytest -v
```

Подробности проверки и сопоставление с чек-листом – в `REPORT_PR10.md`.

## Формы Django (ПР11)

Соответствие сущностей методички проекту то же, что в ПР10: `Room` → `rooms.Room`, «пользователь» → `teachers.Teacher`, `Booking` → `lessons.Lesson`. Правило «одно помещение – одно активное бронирование на дату» превращается в правило «аудитория и преподаватель ведут одно проводимое занятие в день и время». Так как в расписании нет дат, проверка «дата не в прошлом» заменена проверкой учебного времени начала (08:00–21:00).

### Формы

| Форма | Тип | Где | Назначение |
| --- | --- | --- | --- |
| `LessonFilterForm` | `forms.Form` | `dbpages/forms.py` | фильтры списка `/db/lessons/` (GET): день, преподаватель, аудитория, предмет, сортировка |
| `LessonForm` | `forms.ModelForm` | `lessons/forms.py` | создание и редактирование занятия (поле `status` в форме нет) |
| `RoomForm` | `forms.ModelForm` | `rooms/forms.py` | создание и редактирование аудитории, загрузка изображения |

* Имена полей фильтра совпадают с прежними GET-параметрами (`day`, `teacher`, `room`, `q`, `sort`), ссылки и пагинация не изменились. Выборка по-прежнему начинается с `Lesson.objects.active()`, сортировка идёт по белому списку `SORT_FIELDS`, `annotate()`, `values()` и `Paginator` сохранены. Если форма не прошла проверку, фильтры не применяются, а над списком выводятся ошибки.
* `SafeModelChoiceField` не пропускает в запрос к базе «мусорные» идентификаторы (`abc`, `-1`, слишком длинные числа).

### Валидация

* валидатор-функция `validate_duration()` (длительность больше 0 и не более 8 ч);
* стандартный `RegexValidator` для номера аудитории;
* `LessonForm.clean_start_time()` – учебное время; `RoomForm.clean_image()` – размер (до 2 МБ) и формат (JPEG, PNG, GIF, WEBP) по содержимому файла;
* `LessonForm.clean()` – доступность аудитории и преподавателя среди проводимых занятий (`Lesson.objects.active().at(...).exists()`); при редактировании занятие исключается из проверки через `exclude(pk=...)`; ошибки показываются общим блоком (`non_field_errors`), ошибки полей – под полями;
* ограничения базы данных остаются последней защитой от гонки запросов: `IntegrityError` при сохранении превращается в сообщение формы.

### Отмена занятия

В `Lesson` добавлено поле `status` (`Lesson.Status`: «Проводится» / «Отменено»), метод `cancel()` и `LessonQuerySet.active()`. Отмена не удаляет запись: представление `lesson_cancel()` разрешает только POST (`@require_POST`, на GET отвечает 405), форма на странице занятия содержит `{% csrf_token %}`. Отменённое занятие скрыто в списках, счётчиках, статистике и поиске свободных аудиторий, не открывается по прямому адресу (404) и не блокирует аудиторию и преподавателя: уникальные ограничения `unique_active_room_slot` и `unique_active_teacher_slot` стали условными (`condition=Q(status="active")`). В админке отменённые занятия видны, есть фильтр по статусу и действие «Отменить выбранные занятия». Миграция: `lessons/0003_lesson_status.py`.

### Изображения аудиторий

`Room.image` (`ImageField`, `upload_to="rooms/"`, миграция `rooms/0006_room_image.py`), `MEDIA_URL = "/media/"`, `MEDIA_ROOT = BASE_DIR / "media"` (каталог в `.gitignore`). Форма отправляется с `enctype="multipart/form-data"`, в `RoomForm` передаются `request.POST` и `request.FILES`. Так как по умолчанию `DEBUG = False`, а помощник `static()` в этом режиме ничего не добавляет, медиафайлы отдаёт маршрут `/media/<путь>` (`homepage.views.serve_media`) – как и статику, только для учёбы. Изображение выводится на странице аудитории, загружать его можно и в админке.

### Установка и проверка

```text
pip install -r requirements.txt           # добавилась Pillow
python manage.py migrate                  # lessons/0003, rooms/0006
python manage.py check
python manage.py makemigrations --check
python manage.py test
pytest -v
flake8 . --extend-exclude=venv
```

Подробности и таблица проверок – в `REPORT_PR11.md`.

## Текущее состояние и план развития

Реализовано (ПР11):

* формы Django: `LessonFilterForm`, `LessonForm`, `RoomForm`, их валидация и вывод ошибок;
* создание, редактирование и отмена занятий (статус, `POST` + CSRF), условные ограничения уникальности;
* загрузка и вывод изображений аудиторий (`ImageField`, `MEDIA_ROOT`);
* тесты форм, представлений, CSRF и загрузки файлов.

Реализовано (ПР10):

* настроена административная панель (`Room`, `Teacher`, `Subject`, `Lesson`) с русскоязычными названиями, поиском, фильтрами, сортировкой, inline-таблицами и массовыми действиями;
* slug и `get_absolute_url()` аудиторий, `GeneratedField` `is_large`, `TextChoices` типа занятия, `LessonQuerySet`;
* контекстный процессор `room_context`, подключение Django Debug Toolbar, статистика по типам занятий;
* тесты админки, slug, вычисляемого поля, менеджера и процессора.



Реализовано (ПР9):

* Django-модели `Teacher`, `Room`, `Subject`, `Lesson` со связями `ForeignKey` (`on_delete=PROTECT`, `related_name`), ограничениями и абстрактной моделью `TimeStampedModel`;
* миграции и перенос данных из базы ПР7 с сохранением ключей и связей;
* все страницы сайта получают данные через ORM; прямых SQL-запросов в представлениях нет;
* фильтрация, сортировка с белым списком полей, поиск и постраничный вывод занятий (`/db/lessons/`), поиск свободных аудиторий (`/rooms/free/`), статистика через `aggregate()` и `annotate()`;
* тесты на временной базе Django, регистрация моделей в админке.

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

* формы для преподавателей и предметов (сейчас они добавляются в админке);
* использование отложенной логики ПР3 (`add_lesson()`, `delete_lesson()`, поиск, фильтрация по дню, сортировка);
* фильтрация по преподавателю;
* экспорт расписания в CSV/ICS;
* учёт чётности недели (числитель/знаменатель);
* CI.
