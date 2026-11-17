"""Маршруты приложения rooms (подключены с префиксом rooms/)."""

from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.room_list, name="list"),
    # Статический маршрут стоит раньше динамического <int:room_id>/.
    path("free/", views.free_rooms, name="free"),
    # create/ — тоже статический маршрут: он должен стоять раньше
    # <slug:slug>/, иначе слово «create» будет принято за slug.
    path("create/", views.room_create, name="create"),
    path("<int:room_id>/edit/", views.room_update, name="update"),
    path("<int:room_id>/", views.room_detail, name="detail"),
    # Адрес по slug (ПР10): /rooms/auditoriya-301-1/. Числовой slug
    # невозможен (он начинается с «auditoriya-»), поэтому маршруты не
    # пересекаются.
    path("<slug:slug>/", views.room_detail_by_slug, name="slug_detail"),
]
