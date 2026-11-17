"""Общие настройки Django Admin (ПР10).

В приложении «Главная» нет моделей с таблицами (TimeStampedModel
абстрактная), поэтому здесь регистрировать нечего: модели регистрируются
в admin.py приложений lessons, teachers и rooms. Файл задаёт только
заголовки административной панели.
"""

from django.contrib import admin

admin.site.site_header = "Roomly: администрирование"
admin.site.site_title = "Roomly"
admin.site.index_title = "Управление расписанием"
