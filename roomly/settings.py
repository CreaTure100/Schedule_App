"""Настройки Django-проекта roomly («Расписание занятий»)."""

import importlib.util
import os
from pathlib import Path

from db.database import DB_PATH

# Корень репозитория (там же лежат manage.py, main.py, models/, data/).
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = (
    'django-insecure-bm1u6vzgcrvi7ftqqny8q02z3xcrjnu0lxi_bso8c19nf01-bl'
)

# По умолчанию DEBUG = False: так видна своя страница 404 (handler404).
# Статика при этом отдаётся маршрутом static/ из roomly/urls.py.
# Отладку можно включить переменной окружения ROOMLY_DEBUG=1.
DEBUG = os.environ.get("ROOMLY_DEBUG") == "1"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Приложения проекта
    'homepage.apps.HomepageConfig',
    'lessons.apps.LessonsConfig',
    'teachers.apps.TeachersConfig',
    'rooms.apps.RoomsConfig',
    'dbpages.apps.DbpagesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'roomly.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ПР10: site_name и rooms_total во всех шаблонах.
                'rooms.context_processors.room_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'roomly.wsgi.application'


# ПР9: страницы сайта получают данные через Django ORM. Модели —
# Teacher, Room, Subject и Lesson, структура таблиц создаётся
# миграциями (python manage.py migrate), а данные переносятся из базы
# ПР7 командой python -m db.import_sqlite_to_orm.
#
# База Django — db.sqlite3 (см. DATABASES ниже). Исходная база ПР7
# data/roomly.sqlite остаётся источником данных для переноса и в
# DATABASES не подключается. Слой sqlite3 из ПР7 (пакет db/, sql/)
# сохранён как предыдущая реализация; страницы его больше не используют.
SQLITE_PATH = DB_PATH  # исходная база ПР7 (источник для переноса)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]


# Локализация
LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ПР10: Django Debug Toolbar — панель анализа SQL-запросов страниц.
# Подключается только при ROOMLY_DEBUG=1 (Windows PowerShell:
# $env:ROOMLY_DEBUG = "1") и только если пакет установлен
# (pip install django-debug-toolbar). Без этого проект работает как
# раньше, а тесты не зависят от панели.
INTERNAL_IPS = ["127.0.0.1"]
USE_DEBUG_TOOLBAR = (
    DEBUG and importlib.util.find_spec("debug_toolbar") is not None
)
if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ["debug_toolbar"]
    # Middleware панели ставится как можно раньше.
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
