-- Скрипт для проверки данных в таблицах системы мониторинга вакансий
-- Используется схема: msod7

-- 1. Проверка количества записей в таблицах
SELECT '1. Количество записей в таблицах' as "Проверка";

SELECT 
    'business_roles' as "Таблица",
    COUNT(*) as "Количество записей"
FROM msod7.business_roles

UNION ALL

SELECT 
    'skills' as "Таблица",
    COUNT(*) as "Количество записей"
FROM msod7.skills

UNION ALL

SELECT 
    'vacancies' as "Таблица",
    COUNT(*) as "Количество записей"
FROM msod7.vacancies

UNION ALL

SELECT 
    'students' as "Таблица",
    COUNT(*) as "Количество записей"
FROM msod7.students

UNION ALL

SELECT 
    'vacancy_skills' as "Таблица (связи)",
    COUNT(*) as "Количество записей"
FROM msod7.vacancy_skills

UNION ALL

SELECT 
    'student_skills' as "Таблица (связи)",
    COUNT(*) as "Количество записей"
FROM msod7.student_skills

ORDER BY "Таблица";

-- 2. Содержимое таблицы business_roles (бизнес-роли)
SELECT '2. Бизнес-роли' as "Проверка";

SELECT 
    id,
    name as "Название роли",
    description as "Описание",
    created_at as "Дата создания"
FROM msod7.business_roles
ORDER BY id;

-- 3. Содержимое таблицы skills (навыки)
SELECT '3. Навыки (первые 20 записей)' as "Проверка";

SELECT 
    id,
    name as "Название навыка",
    category as "Категория",
    created_at as "Дата создания"
FROM msod7.skills
ORDER BY id
LIMIT 20;

-- 4. Проверка вакансий с группировкой по бизнес-ролям
SELECT '4. Вакансии по бизнес-ролям' as "Проверка";

SELECT 
    br.name as "Бизнес-роль",
    COUNT(v.id) as "Количество вакансий"
FROM msod7.business_roles br
LEFT JOIN msod7.vacancies v ON br.id = v.business_role_id
GROUP BY br.id, br.name
ORDER BY COUNT(v.id) DESC;

-- 5. Последние 10 вакансий
SELECT '5. Последние 10 вакансий' as "Проверка";

SELECT 
    v.id,
    v.hh_id as "ID на HH",
    v.title as "Должность",
    v.company as "Компания",
    CASE 
        WHEN v.salary_from IS NOT NULL OR v.salary_to IS NOT NULL 
        THEN CONCAT(
            COALESCE(v.salary_from::text, '?'), 
            ' - ', 
            COALESCE(v.salary_to::text, '?'), 
            ' ', 
            COALESCE(v.currency, '')
        )
        ELSE 'не указана'
    END as "Зарплата",
    v.area as "Город",
    v.experience as "Опыт",
    br.name as "Бизнес-роль",
    v.published_at as "Дата публикации",
    v.created_at as "Дата добавления в БД"
FROM msod7.vacancies v
LEFT JOIN msod7.business_roles br ON v.business_role_id = br.id
ORDER BY v.id DESC
LIMIT 10;

-- 6. Статистика по вакансиям
SELECT '6. Статистика по вакансиям' as "Проверка";

-- Общее количество вакансий
WITH stats AS (
    SELECT 
        COUNT(*) as total_vacancies,
        COUNT(CASE WHEN salary_from IS NOT NULL OR salary_to IS NOT NULL THEN 1 END) as with_salary,
        AVG(
            CASE 
                WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL 
                THEN (salary_from + salary_to) / 2 
            END
        ) as avg_salary
    FROM msod7.vacancies
)
SELECT 
    total_vacancies as "Всего вакансий",
    with_salary as "С указанием зарплаты",
    ROUND(avg_salary) as "Средняя зарплата"
FROM stats;

-- 7. Топ 10 самых частых навыков в вакансиях
SELECT '7. Топ 10 навыков в вакансиях' as "Проверка";

SELECT 
    s.name as "Навык",
    COUNT(vs.vacancy_id) as "Количество вакансий",
    s.category as "Категория"
FROM msod7.skills s
JOIN msod7.vacancy_skills vs ON s.id = vs.skill_id
GROUP BY s.id, s.name, s.category
ORDER BY COUNT(vs.vacancy_id) DESC
LIMIT 10;

-- 8. Вакансии с наибольшим количеством навыков
SELECT '8. Вакансии с наибольшим количеством навыков' as "Проверка";

SELECT 
    v.title as "Должность",
    v.company as "Компания",
    COUNT(vs.skill_id) as "Количество навыков",
    STRING_AGG(s.name, ', ') as "Навыки"
FROM msod7.vacancies v
JOIN msod7.vacancy_skills vs ON v.id = vs.vacancy_id
JOIN msod7.skills s ON vs.skill_id = s.id
GROUP BY v.id, v.title, v.company
ORDER BY COUNT(vs.skill_id) DESC
LIMIT 10;

-- 9. Проверка студентов и их навыков
SELECT '9. Студенты и их навыки' as "Проверка";

SELECT 
    st.id as "ID студента",
    st.name as "Имя студента",
    st.email as "Email",
    br.name as "Бизнес-роль студента",
    COUNT(ss.skill_id) as "Количество навыков",
    STRING_AGG(s.name, ', ') as "Навыки"
FROM msod7.students st
LEFT JOIN msod7.business_roles br ON st.business_role_id = br.id
LEFT JOIN msod7.student_skills ss ON st.id = ss.student_id
LEFT JOIN msod7.skills s ON ss.skill_id = s.id
GROUP BY st.id, st.name, st.email, br.name
ORDER BY st.id;

-- 10. Проверка вакансий без бизнес-роли
SELECT '10. Вакансии без назначенной бизнес-роли' as "Проверка";

SELECT 
    COUNT(*) as "Количество вакансий без бизнес-роли"
FROM msod7.vacancies
WHERE business_role_id IS NULL;

-- 11. Проверка вакансий без навыков
SELECT '11. Вакансии без указанных навыков' as "Проверка";

SELECT 
    v.id,
    v.title,
    v.company,
    v.created_at
FROM msod7.vacancies v
LEFT JOIN msod7.vacancy_skills vs ON v.id = vs.vacancy_id
WHERE vs.vacancy_id IS NULL
ORDER BY v.created_at DESC
LIMIT 10;

-- 12. Проверка целостности данных (вакансии с несуществующей бизнес-ролью)
SELECT '12. Проверка целостности: вакансии с несуществующей бизнес-ролью' as "Проверка";

SELECT 
    v.id,
    v.title,
    v.business_role_id
FROM msod7.vacancies v
LEFT JOIN msod7.business_roles br ON v.business_role_id = br.id
WHERE v.business_role_id IS NOT NULL AND br.id IS NULL;

-- 13. Динамика добавления вакансий по дням
SELECT '13. Динамика добавления вакансий по дням' as "Проверка";

SELECT 
    DATE(created_at) as "Дата",
    COUNT(*) as "Количество вакансий"
FROM msod7.vacancies
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC
LIMIT 14;

-- 14. Разбивка вакансий по городам (топ 10)
SELECT '14. Топ 10 городов по количеству вакансий' as "Проверка";

SELECT 
    COALESCE(area, 'Не указан') as "Город",
    COUNT(*) as "Количество вакансий",
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM msod7.vacancies), 2) as "Процент"
FROM msod7.vacancies
GROUP BY area
ORDER BY COUNT(*) DESC
LIMIT 10;

-- 15. Проверка дубликатов вакансий по hh_id
SELECT '15. Проверка дубликатов вакансий (по hh_id)' as "Проверка";

SELECT 
    hh_id,
    COUNT(*) as "Количество дубликатов"
FROM msod7.vacancies
WHERE hh_id IS NOT NULL
GROUP BY hh_id
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 10;

-- 16. Сводная таблица: вакансии по бизнес-ролям и опыту работы
SELECT '16. Вакансии по бизнес-ролям и требуемому опыту' as "Проверка";

SELECT 
    br.name as "Бизнес-роль",
    v.experience as "Требуемый опыт",
    COUNT(*) as "Количество вакансий",
    ROUND(AVG(
        CASE 
            WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
            THEN (v.salary_from + v.salary_to) / 2 
        END
    )) as "Средняя зарплата"
FROM msod7.vacancies v
JOIN msod7.business_roles br ON v.business_role_id = br.id
WHERE v.experience IS NOT NULL AND v.experience != ''
GROUP BY br.name, v.experience
ORDER BY br.name, 
    CASE v.experience
        WHEN 'нет опыта' THEN 1
        WHEN 'менее года' THEN 2
        WHEN 'от 1 года до 3 лет' THEN 3
        WHEN 'от 3 до 6 лет' THEN 4
        WHEN 'более 6 лет' THEN 5
        ELSE 6
    END;
