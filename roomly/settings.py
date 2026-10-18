"""Настройки Django-проекта roomly («Расписание занятий»)."""

from pathlib import Path

# Корень репозитория (там же лежат manage.py, main.py, models/, data/).
BASE_DIR = Path(__file__).resolve().parent.parent

# Учебный проект: ключ можно хранить в репозитории. В реальном проекте
# его выносят в переменную окружения.
SECRET_KEY = (
    'django-insecure-bm1u6vzgcrvi7ftqqny8q02z3xcrjnu0lxi_bso8c19nf01-bl'
)

# DEBUG = False нужен, чтобы увидеть свою страницу 404 (handler404).
# После проверки верните DEBUG = True для удобной разработки.
DEBUG = False

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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'roomly.wsgi.application'


# База данных нужна встроенным приложениям Django (admin, auth, sessions).
# Данные расписания по-прежнему лежат в data/schedule.json.
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
