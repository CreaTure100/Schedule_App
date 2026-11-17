"""Форма создания и редактирования аудитории с изображением (ПР11).

RoomForm — ModelForm на основе модели Room. В списке полей нет slug и
is_large: slug создаёт save(), а is_large вычисляет база данных.
Изображение проверяется стандартным ImageField (файл должен быть
картинкой) и дополнительно clean_image() (формат и размер).
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import RegexValidator

from rooms.models import Room

# Наибольший размер загружаемого файла, байт (2 МБ).
MAX_IMAGE_SIZE = 2 * 1024 * 1024

# Допустимые форматы изображения (по содержимому, а не по расширению).
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}

# Номер аудитории: буквы, цифры и дефис («301», «12а», «А-101»).
number_validator = RegexValidator(
    r"^[\w-]+$",
    "Номер может содержать только буквы, цифры и дефис.",
)


class RoomForm(forms.ModelForm):
    """Аудитория: номер, этаж, вместимость и изображение."""

    number = forms.CharField(
        max_length=20,
        label="Номер аудитории",
        validators=[number_validator],
        # Явно объявленное поле не берёт Meta.error_messages, поэтому
        # сообщение о нарушении уникальности (код unique) задано здесь.
        error_messages={"unique": "Аудитория с таким номером уже есть."},
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Room
        fields = ["number", "floor", "capacity", "image"]
        widgets = {
            "floor": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}),
            "capacity": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}),
            "image": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}),
        }
        help_texts = {
            "capacity": "Необязательно. От 50 мест аудитория «большая».",
            "image": "JPEG, PNG, GIF или WEBP, не более 2 МБ.",
        }

    def clean_image(self):
        """Проверить размер и формат загруженного файла.

        Расширению из имени файла доверять нельзя: формат берётся из
        содержимого (его определяет Pillow при проверке ImageField).
        Прежнее изображение при редактировании не проверяется заново.
        """
        image = self.cleaned_data.get("image")
        if isinstance(image, UploadedFile):
            if image.size > MAX_IMAGE_SIZE:
                raise ValidationError(
                    "Файл слишком большой: не более 2 МБ.")
            picture = getattr(image, "image", None)
            if picture is not None and picture.format not in (
                    ALLOWED_IMAGE_FORMATS):
                raise ValidationError(
                    "Допустимы изображения JPEG, PNG, GIF и WEBP.")
        return image
