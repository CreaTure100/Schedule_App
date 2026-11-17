"""Маршруты приложения rooms (подключены с префиксом rooms/)."""

from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.room_list, name="list"),
    # Статический маршрут стоит раньше динамического <int:room_id>/.
    path("free/", views.free_rooms, name="free"),
    path("<int:room_id>/", views.room_detail, name="detail"),
]
