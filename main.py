import json
import os

DATA_FILE = "schedule.json"

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]


def load_schedule():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule(schedule):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def show_schedule(schedule):
    if not schedule:
        print("\nРасписание пусто.\n")
        return
    print("\n===== РАСПИСАНИЕ =====")
    for i, lesson in enumerate(schedule, 1):
        print(f"{i}. {lesson['day']} | {lesson['time']} | "
              f"{lesson['subject']} | преподаватель: {lesson['teacher']} | ауд. {lesson['room']}")
    print()


def add_lesson(schedule):
    print("\nДни недели:")
    for i, d in enumerate(DAYS, 1):
        print(f"  {i}. {d}")
    try:
        day_idx = int(input("Выберите номер дня: ")) - 1
        if not (0 <= day_idx < len(DAYS)):
            print("Неверный номер дня.\n")
            return
    except ValueError:
        print("Нужно ввести число.\n")
        return

    time = input("Время (например, 10:00): ").strip()
    subject = input("Предмет: ").strip()
    teacher = input("Преподаватель: ").strip()
    room = input("Аудитория: ").strip()

    if not subject:
        print("Предмет не может быть пустым.\n")
        return

    schedule.append({
        "day": DAYS[day_idx],
        "time": time,
        "subject": subject,
        "teacher": teacher,
        "room": room,
    })
    save_schedule(schedule)
    print("Занятие добавлено.\n")


def delete_lesson(schedule):
    show_schedule(schedule)
    if not schedule:
        return
    try:
        idx = int(input("Введите номер занятия для удаления: ")) - 1
        if 0 <= idx < len(schedule):
            removed = schedule.pop(idx)
            save_schedule(schedule)
            print(f"🗑 Удалено: {removed['subject']}\n")
        else:
            print("Неверный номер.\n")
    except ValueError:
        print("Нужно ввести число.\n")


def main():
    schedule = load_schedule()
    while True:
        print("===== МЕНЮ =====")
        print("1. Показать расписание")
        print("2. Добавить занятие")
        print("3. Удалить занятие")
        print("0. Выход")
        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            show_schedule(schedule)
        elif choice == "2":
            add_lesson(schedule)
        elif choice == "3":
            delete_lesson(schedule)
        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неизвестная команда.\n")


if __name__ == "__main__":
    main()