"""Точка входа приложения «Расписание занятий»."""

from datetime import date

from schedule import (
    DAYS, add_lesson, delete_lesson, find_lessons,
    filter_lessons_by_day, sort_lessons_by_time, get_day_status,
)
from storage import load_schedule, save_schedule
from utils import input_int, input_nonempty


def show_schedule(schedule: list[dict]) -> None:
    """Вывести расписание в виде таблицы."""
    if not schedule:
        print("\nРасписание пусто.\n")
        return
    print("\n===== РАСПИСАНИЕ =====")
    for i, lesson in enumerate(schedule, 1):
        print(f"{i}. {lesson['day']} | {lesson['time']} | "
              f"{lesson['subject']} | {lesson['teacher']} | ауд. {lesson['room']}")
    print()


def show_day_status() -> None:
    """Показать статус выбранного дня."""
    print("\nДни недели:")
    for i, d in enumerate(DAYS, 1):
        print(f"  {i}. {d}")
    idx = input_int("Выберите номер дня: ", 1, len(DAYS)) - 1
    print(get_day_status(DAYS[idx], date.today()), "\n")


def handle_add(schedule: list[dict]) -> None:
    """Добавить занятие через меню."""
    print("\nДни недели:")
    for i, d in enumerate(DAYS, 1):
        print(f"  {i}. {d}")
    idx = input_int("Выберите номер дня: ", 1, len(DAYS)) - 1
    time = input_nonempty("Время (например, 10:00): ")
    subject = input_nonempty("Предмет: ")
    teacher = input_nonempty("Преподаватель: ")
    room = input_nonempty("Аудитория: ")
    add_lesson(schedule, DAYS[idx], time, subject, teacher, room)
    save_schedule(schedule)
    print("Занятие добавлено.\n")


def handle_delete(schedule: list[dict]) -> None:
    """Удалить занятие через меню."""
    show_schedule(schedule)
    if not schedule:
        return
    idx = input_int("Введите номер занятия для удаления: ",
                    1, len(schedule)) - 1
    removed = delete_lesson(schedule, idx)
    if removed:
        save_schedule(schedule)
        print(f"Удалено: {removed['subject']}\n")


def handle_find(schedule: list[dict]) -> None:
    """Найти занятия по подстроке."""
    query = input_nonempty("Что искать в названии предмета: ")
    found = find_lessons(schedule, query)
    show_schedule(found)


def handle_filter_by_day(schedule: list[dict]) -> None:
    """Показать занятия на выбранный день."""
    print("\nДни недели:")
    for i, d in enumerate(DAYS, 1):
        print(f"  {i}. {d}")
    idx = input_int("Выберите номер дня: ", 1, len(DAYS)) - 1
    show_schedule(filter_lessons_by_day(schedule, DAYS[idx]))


def handle_sort(schedule: list[dict]) -> None:
    """Показать занятия, отсортированные по времени."""
    show_schedule(sort_lessons_by_time(schedule))


def main() -> None:
    """Точка запуска: меню приложения."""
    schedule = load_schedule()
    while True:
        print("===== МЕНЮ =====")
        print("1. Показать расписание")
        print("2. Добавить занятие")
        print("3. Удалить занятие")
        print("4. Найти занятие по предмету")
        print("5. Показать занятия на день")
        print("6. Показать по времени (сортировка)")
        print("7. Статус дня")
        print("0. Выход")
        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            show_schedule(schedule)
        elif choice == "2":
            handle_add(schedule)
        elif choice == "3":
            handle_delete(schedule)
        elif choice == "4":
            handle_find(schedule)
        elif choice == "5":
            handle_filter_by_day(schedule)
        elif choice == "6":
            handle_sort(schedule)
        elif choice == "7":
            show_day_status()
        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неизвестная команда.\n")


if __name__ == "__main__":
    main()
