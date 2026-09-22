"""Вспомогательные функции ввода с обработкой ошибок."""

from datetime import date, datetime


def input_int(prompt: str, min_value: int = 0, max_value: int = 10**9) -> int:
    """Запросить целое число в диапазоне [min_value, max_value]."""
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("Ошибка: нужно ввести целое число. Повторите ввод.")
            continue
        if not (min_value <= value <= max_value):
            print(f"Ошибка: число должно быть в диапазоне "
                  f"{min_value}..{max_value}. Повторите ввод.")
            continue
        return value


def input_nonempty(prompt: str) -> str:
    """Запросить непустую строку."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Ошибка: строка не может быть пустой. Повторите ввод.")


def input_date(prompt: str) -> date:
    """Запросить дату в формате ДД.ММ.ГГГГ."""
    while True:
        raw = input(prompt).strip()
        try:
            return datetime.strptime(raw, "%d.%m.%Y").date()
        except ValueError:
            print("Ошибка: неверный формат даты. Ожидается ДД.ММ.ГГГГ.")
