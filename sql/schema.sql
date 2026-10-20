-- ============================================================
-- Схема базы данных проекта «Система расписания занятий» (Roomly).
-- СУБД: SQLite. Файл базы: data/roomly.sqlite.
--
-- Выполняется командой executescript() (см. db/database.py, init_db)
-- или в SQLite CLI:  .read sql/schema.sql
-- Скрипт можно запускать повторно: везде IF NOT EXISTS.
--
-- Сущности: Teacher -> teachers, Room -> rooms,
--           предмет  -> subjects, Lesson -> lessons.
-- Класс Schedule (расписание) — это набор строк таблицы lessons,
-- поэтому отдельной таблицы он не получает.
-- ============================================================

-- Преподаватели. Ключ в JSON — имя («Иванов И.И.»).
CREATE TABLE IF NOT EXISTS teachers (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT    NOT NULL UNIQUE,   -- «Иванов И.И.»
    surname   TEXT    NOT NULL,          -- «Иванов» (для поиска и сортировки)
    email     TEXT                       -- необязателен: в JSON его нет
);

-- Аудитории. Номер — строка («301», «12а»), поэтому TEXT.
CREATE TABLE IF NOT EXISTS rooms (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    number   TEXT    NOT NULL UNIQUE,    -- «301»
    floor    INTEGER,                    -- этаж; NULL, если номер нечисловой
    capacity INTEGER                     -- вместимость; необязательна
             CHECK (capacity IS NULL OR capacity > 0)
);

-- Предметы (справочник): одно название хранится один раз.
CREATE TABLE IF NOT EXISTS subjects (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE           -- «Физика»
);

-- Занятия: день, время, предмет, преподаватель, аудитория.
CREATE TABLE IF NOT EXISTS lessons (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    day            TEXT    NOT NULL      -- день недели, как в JSON
                   CHECK (day IN ('Понедельник', 'Вторник', 'Среда',
                                  'Четверг', 'Пятница', 'Суббота')),
    day_number     INTEGER NOT NULL      -- 1..6: порядок дней для ORDER BY
                   CHECK (day_number BETWEEN 1 AND 6),
    start_time     TEXT    NOT NULL      -- «ЧЧ:ММ», сортируется как текст
                   CHECK (start_time GLOB '[0-2][0-9]:[0-5][0-9]'),
    duration_hours REAL    NOT NULL DEFAULT 1.5
                   CHECK (duration_hours > 0),
    lesson_type    TEXT,                 -- «лабораторная»; NULL — обычное
    subject_id     INTEGER NOT NULL,
    teacher_id     INTEGER NOT NULL,
    room_id        INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (room_id) REFERENCES rooms (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    -- Аудитория и преподаватель не могут вести два занятия одновременно.
    UNIQUE (day_number, start_time, room_id),
    UNIQUE (day_number, start_time, teacher_id)
);

-- Индексы по внешним ключам ускоряют JOIN и GROUP BY.
CREATE INDEX IF NOT EXISTS idx_lessons_subject ON lessons (subject_id);
CREATE INDEX IF NOT EXISTS idx_lessons_teacher ON lessons (teacher_id);
CREATE INDEX IF NOT EXISTS idx_lessons_room    ON lessons (room_id);
