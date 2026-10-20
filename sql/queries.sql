-- ============================================================
-- SQL-запросы к базе data/roomly.sqlite («Система расписания занятий»).
--
-- Как проверить запрос в SQLite CLI (из корня проекта):
--     sqlite3 data/roomly.sqlite
--     sqlite> .headers on
--     sqlite> .mode column
--     sqlite> .read sql/queries.sql        -- выполнить все запросы сразу
-- или скопировать один запрос в консоль sqlite3.
-- Без CLI те же запросы выполняет:  python -m db.check --queries
--
-- Формат заголовка:  -- Запрос N [ТЕГИ]. Назначение.
-- Теги: ORDER, WHERE, JOIN, AGGREGATE, GROUP, LIMIT, SUBQUERY.
-- Во всех запросах значения заданы литералами только для проверки в CLI;
-- в Django-представлениях те же запросы получают значения через «?».
-- Примечание: LIKE и lower() в SQLite не различают регистр лишь у
-- латиницы, поэтому кириллические шаблоны пишутся с учётом регистра.
-- ============================================================


-- ---------- Выборка списков: SELECT + ORDER BY ----------

-- Запрос 1 [ORDER]. Преподаватели по алфавиту фамилий.
-- Ожидается: 7 строк, первая — Иванов И.И., последняя — Смирнов А.А.
SELECT id, full_name, surname
FROM teachers
ORDER BY surname, full_name;

-- Запрос 2 [ORDER]. Занятия в порядке недели: день, затем время.
-- Ожидается: 16 строк, первая — Понедельник 09:00, последняя — Суббота 11:45.
SELECT id, day, start_time, lesson_type
FROM lessons
ORDER BY day_number, start_time;

-- Запрос 3 [ORDER, LIMIT]. Аудитории с верхних этажей, постранично
-- (LIMIT — размер страницы, OFFSET — сколько строк пропустить).
-- Ожидается: 3 строки (402, 401, 305) — первая страница из трёх.
-- Вторая страница: LIMIT 3 OFFSET 3.
SELECT number, floor
FROM rooms
ORDER BY floor DESC, number DESC
LIMIT 3 OFFSET 0;


-- ---------- Фильтрация: WHERE ----------

-- Запрос 4 [WHERE]. Занятия в понедельник, начинающиеся не раньше 10:00
-- (условие с AND).
-- Ожидается: 2 строки (10:45 и 13:00).
SELECT id, day, start_time, subject_id
FROM lessons
WHERE day = 'Понедельник' AND start_time >= '10:00'
ORDER BY start_time;

-- Запрос 5 [WHERE]. Занятия, начинающиеся между 09:00 и 10:00
-- включительно (BETWEEN).
-- Ожидается: 6 строк (пять занятий в 09:00 и суббота 10:00).
SELECT id, day, start_time
FROM lessons
WHERE start_time BETWEEN '09:00' AND '10:00'
ORDER BY day_number, start_time;

-- Запрос 6 [WHERE]. Занятия в среду и пятницу, кроме самых ранних
-- (IN, NOT, AND).
-- Ожидается: 3 строки: среда 10:45 и 14:15, пятница 10:45.
SELECT id, day, start_time
FROM lessons
WHERE day IN ('Среда', 'Пятница') AND NOT start_time < '10:00'
ORDER BY day_number, start_time;

-- Запрос 7 [WHERE]. Предметы, название которых начинается с «Хим»
-- или содержит «Python» (LIKE, OR).
-- Ожидается: 2 строки — Программирование на Python, Химия.
SELECT id, title
FROM subjects
WHERE title LIKE 'Хим%' OR title LIKE '%Python%'
ORDER BY title;

-- Запрос 8 [WHERE]. Занятия с указанным типом (IS NOT NULL);
-- у обычных занятий lesson_type равен NULL (проверка — IS NULL).
-- Ожидается: 1 строка — суббота 10:00, лабораторная.
SELECT id, day, start_time, lesson_type
FROM lessons
WHERE lesson_type IS NOT NULL;

-- Запрос 9 [WHERE]. Преподаватели, для которых не заполнен e-mail
-- (IS NULL): e-mail в JSON не хранится, поэтому NULL у всех.
-- Ожидается: 7 строк.
SELECT id, full_name
FROM teachers
WHERE email IS NULL
ORDER BY surname;


-- ---------- Соединение таблиц: JOIN ----------

-- Запрос 10 [JOIN]. Занятия с названиями предметов (JOIN двух таблиц).
-- Ожидается: 16 строк.
SELECT l.day, l.start_time, s.title AS subject
FROM lessons AS l
JOIN subjects AS s ON s.id = l.subject_id
ORDER BY l.day_number, l.start_time;

-- Запрос 11 [JOIN]. Кто и где ведёт занятия: преподаватель и аудитория
-- (JOIN трёх таблиц).
-- Ожидается: 16 строк.
SELECT l.day, l.start_time, t.full_name AS teacher, r.number AS room
FROM lessons AS l
JOIN teachers AS t ON t.id = l.teacher_id
JOIN rooms AS r ON r.id = l.room_id
ORDER BY l.day_number, l.start_time;

-- Запрос 12 [JOIN, ORDER]. Полное расписание: день, время, предмет,
-- тип, преподаватель, аудитория (JOIN четырёх таблиц). Этот же запрос
-- выполняет страница «Занятия» в разделе «База данных».
-- Ожидается: 16 строк.
SELECT l.id, l.day, l.start_time, s.title AS subject, l.lesson_type,
       t.full_name AS teacher, r.number AS room
FROM lessons AS l
JOIN subjects AS s ON s.id = l.subject_id
JOIN teachers AS t ON t.id = l.teacher_id
JOIN rooms AS r ON r.id = l.room_id
ORDER BY l.day_number, l.start_time;


-- ---------- Агрегатные функции ----------

-- Запрос 13 [AGGREGATE]. Общая сводка по занятиям: COUNT, MIN, MAX.
-- Ожидается: 1 строка: 16 занятий, 7 преподавателей, 7 аудиторий,
-- самое раннее начало 09:00, самое позднее 14:15.
SELECT COUNT(*) AS lessons_count,
       COUNT(DISTINCT teacher_id) AS teachers_count,
       COUNT(DISTINCT room_id) AS rooms_count,
       MIN(start_time) AS first_start,
       MAX(start_time) AS last_start
FROM lessons;

-- Запрос 14 [AGGREGATE]. Нагрузка: SUM и AVG по длительности занятий;
-- COUNT(lesson_type) считает только непустые значения.
-- Ожидается: 1 строка: 24.0 часа всего, 1.5 в среднем, 1 занятие с типом.
SELECT SUM(duration_hours) AS total_hours,
       AVG(duration_hours) AS avg_hours,
       COUNT(lesson_type) AS typed_lessons
FROM lessons;

-- Запрос 15 [AGGREGATE]. Этажи аудиторий: MIN, MAX, AVG.
-- Ожидается: 1 строка: этажи от 1 до 4, среднее примерно 2.86.
SELECT MIN(floor) AS lowest, MAX(floor) AS highest, AVG(floor) AS average
FROM rooms;


-- ---------- Группировка: GROUP BY, HAVING ----------

-- Запрос 16 [GROUP, JOIN, AGGREGATE]. Число занятий и часов по
-- преподавателям. Используется на странице «Статистика».
-- Ожидается: 7 строк, больше всех у Кузнецова К.К. — 4 занятия, 6.0 ч.
SELECT t.full_name AS teacher,
       COUNT(*) AS lessons_count,
       SUM(l.duration_hours) AS hours
FROM lessons AS l
JOIN teachers AS t ON t.id = l.teacher_id
GROUP BY t.id, t.full_name
ORDER BY lessons_count DESC, t.surname;

-- Запрос 17 [GROUP, AGGREGATE]. Занятия по дням недели: сколько их и
-- когда день начинается и заканчивается.
-- Ожидается: 6 строк (Понедельник — 3 занятия, 09:00–13:00).
SELECT day,
       COUNT(*) AS lessons_count,
       MIN(start_time) AS first_start,
       MAX(start_time) AS last_start
FROM lessons
GROUP BY day_number, day
ORDER BY day_number;

-- Запрос 18 [GROUP, JOIN]. Аудитории, в которых не меньше двух занятий
-- (HAVING фильтрует уже сгруппированные строки).
-- Ожидается: 6 строк (в ауд. 305 одно занятие, она не попадает).
SELECT r.number AS room, COUNT(*) AS lessons_count
FROM lessons AS l
JOIN rooms AS r ON r.id = l.room_id
GROUP BY r.id, r.number
HAVING COUNT(*) >= 2
ORDER BY lessons_count DESC, r.number;

-- Запрос 19 [GROUP, JOIN]. Предметы, которые идут больше одного раза
-- в неделю.
-- Ожидается: 6 строк, у каждого предмета по 2 занятия: Английский язык,
-- История России, Математический анализ, Программирование на Python,
-- Физика, Химия (лекция и лабораторная считаются одним предметом).
SELECT s.title AS subject, COUNT(*) AS lessons_count
FROM lessons AS l
JOIN subjects AS s ON s.id = l.subject_id
GROUP BY s.id, s.title
HAVING COUNT(*) > 1
ORDER BY lessons_count DESC, s.title;


-- ---------- Подзапросы ----------

-- Запрос 20 [SUBQUERY, GROUP, JOIN]. Преподаватели, у которых занятий
-- больше среднего (подзапрос в HAVING).
-- Ожидается: 2 строки: Кузнецов К.К. (4) и Иванов И.И. (3).
SELECT t.full_name AS teacher, COUNT(*) AS lessons_count
FROM lessons AS l
JOIN teachers AS t ON t.id = l.teacher_id
GROUP BY t.id, t.full_name
HAVING COUNT(*) > (SELECT COUNT(*) * 1.0 / COUNT(DISTINCT teacher_id)
                   FROM lessons)
ORDER BY lessons_count DESC;

-- Запрос 21 [SUBQUERY, WHERE]. Преподаватели без занятий (NOT IN).
-- Сейчас результат пустой: преподаватели импортированы из занятий.
-- Чтобы увидеть строку, добавьте преподавателя вручную:
--   INSERT INTO teachers (full_name, surname) VALUES ('Тестов Т.Т.', 'Тестов');
-- и после проверки удалите его:
--   DELETE FROM teachers WHERE full_name = 'Тестов Т.Т.';
-- Ожидается: 0 строк.
SELECT id, full_name
FROM teachers
WHERE id NOT IN (SELECT teacher_id FROM lessons);
