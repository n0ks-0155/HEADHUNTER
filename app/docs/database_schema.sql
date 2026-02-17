-- Обновленная схема базы данных для системы мониторинга вакансий

-- 1. СПРАВОЧНИК КОМПАНИЙ
CREATE TABLE msod7.companies (
    id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE,  
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по названию компании
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_hh_id ON companies(hh_id);

-- 2. СПРАВОЧНИК РЕГИОНОВ (городов)
CREATE TABLE msod7.regions (
    id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE,  -- ID региона на HeadHunter
    name VARCHAR(100) NOT NULL,
    parent_region_id INTEGER REFERENCES regions(id),  -- для иерархии (область/край -> город)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по названию региона
CREATE INDEX idx_regions_name ON regions(name);
CREATE INDEX idx_regions_hh_id ON regions(hh_id);

-- 3. Таблица бизнес-ролей колледжа
CREATE TABLE msod7.business_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Таблица навыков (skills)
CREATE TABLE msod7.skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Таблица вакансий
CREATE TABLE msod7.vacancies (
    id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE,  -- ID вакансии на HeadHunter
    title VARCHAR(255) NOT NULL,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    region_id INTEGER REFERENCES regions(id) ON DELETE SET NULL,
    salary_from INTEGER,
    salary_to INTEGER,
    currency VARCHAR(10),
    experience VARCHAR(50),
    employment_type VARCHAR(50),
    schedule VARCHAR(50),
    description TEXT,
    key_skills TEXT,  -- JSON или текстовое представление навыков
    url VARCHAR(500),
    published_at TIMESTAMP,
    business_role_id INTEGER REFERENCES business_roles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Связь многие-ко-многим: вакансии и навыки
CREATE TABLE msod7.vacancy_skills (
    vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (vacancy_id, skill_id)
);

-- 7. Таблица студентов (для будущих рекомендаций)
CREATE TABLE msod7.students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    business_role_id INTEGER REFERENCES business_roles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Связь многие-ко-многим: студенты и навыки
CREATE TABLE msod7.student_skills (
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 5),
    PRIMARY KEY (student_id, skill_id)
);

-- Индексы для оптимизации
CREATE INDEX idx_vacancies_business_role ON vacancies(business_role_id);
CREATE INDEX idx_vacancies_published_at ON vacancies(published_at);
CREATE INDEX idx_vacancies_salary_from ON vacancies(salary_from);
CREATE INDEX idx_vacancies_company ON vacancies(company_id);
CREATE INDEX idx_vacancies_region ON vacancies(region_id);
CREATE INDEX idx_vacancies_hh_id ON vacancies(hh_id);
CREATE INDEX idx_vacancies_created_at ON vacancies(created_at);

-- Индекс для полнотекстового поиска по названию вакансии
CREATE INDEX idx_vacancies_title_trgm ON vacancies USING gin (title gin_trgm_ops);

-- Триггер для обновления updated_at в vacancies
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vacancies_updated_at 
    BEFORE UPDATE ON vacancies 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Триггер для обновления updated_at в companies
CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON companies 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Представление для удобного просмотра вакансий
CREATE VIEW vacancies_view AS
SELECT 
    v.id,
    v.hh_id,
    v.title,
    c.name as company_name,
    c.id as company_id,
    r.name as region_name,
    r.id as region_id,
    v.salary_from,
    v.salary_to,
    v.currency,
    v.experience,
    v.employment_type,
    v.schedule,
    br.name as business_role_name,
    br.id as business_role_id,
    v.published_at,
    v.created_at,
    v.url
FROM vacancies v
LEFT JOIN companies c ON v.company_id = c.id
LEFT JOIN regions r ON v.region_id = r.id
LEFT JOIN business_roles br ON v.business_role_id = br.id;

-- Функция для получения статистики по вакансиям
CREATE OR REPLACE FUNCTION get_vacancies_statistics()
RETURNS TABLE (
    total_vacancies bigint,
    vacancies_with_salary bigint,
    avg_salary numeric,
    companies_count bigint,
    regions_count bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(v.id) as total_vacancies,
        COUNT(CASE WHEN v.salary_from IS NOT NULL OR v.salary_to IS NOT NULL THEN 1 END) as vacancies_with_salary,
        ROUND(AVG(CASE WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                      THEN (v.salary_from + v.salary_to) / 2 END)) as avg_salary,
        COUNT(DISTINCT v.company_id) as companies_count,
        COUNT(DISTINCT v.region_id) as regions_count
    FROM vacancies v;
END;
$$ LANGUAGE plpgsql;

-- Вставка основных данных для регионов (можно дополнить)
INSERT INTO regions (hh_id, name) VALUES
(113, 'Россия'),
(1, 'Москва'),
(2, 'Санкт-Петербург'),
(22, 'Владивосток'),
(76, 'Новосибирск'),
(66, 'Екатеринбург'),
(4, 'Новосибирская область'),
(3, 'Красноярский край'),
(104, 'Хабаровский край'),
(99, 'Приморский край')
ON CONFLICT (hh_id) DO NOTHING;

-- Вставка основных бизнес-ролей
INSERT INTO business_roles (name, description) VALUES
('Data Analyst', 'Аналитик данных, работа с BI-системами'),
('Frontend Developer', 'Разработка пользовательских интерфейсов'),
('Backend Developer', 'Разработка серверной части приложений'),
('Fullstack Developer', 'Полный цикл разработки приложений'),
('DevOps Engineer', 'Автоматизация процессов разработки и развертывания'),
('QA Engineer', 'Тестирование и обеспечение качества ПО'),
('Project Manager', 'Управление проектами и командами разработки'),
('UX/UI Designer', 'Дизайн пользовательских интерфейсов'),
('Data Scientist', 'Специалист по машинному обучению и анализу данных'),
('System Administrator', 'Администрирование IT-инфраструктуры')
ON CONFLICT (name) DO NOTHING;

-- Вставка основных навыков
INSERT INTO skills (name, category) VALUES
('Python', 'Programming'),
('JavaScript', 'Programming'),
('SQL', 'Database'),
('HTML/CSS', 'Web'),
('React', 'Frontend'),
('Vue.js', 'Frontend'),
('Docker', 'DevOps'),
('Git', 'Tools'),
('PostgreSQL', 'Database'),
('MongoDB', 'Database'),
('Linux', 'Systems'),
('AWS', 'Cloud'),
('Agile', 'Methodology'),
('Scrum', 'Methodology'),
('Figma', 'Design'),
('Tableau', 'Analytics'),
('Power BI', 'Analytics'),
('Kubernetes', 'DevOps'),
('Java', 'Programming'),
('C#', 'Programming'),
('PHP', 'Programming'),
('Ruby', 'Programming'),
('Go', 'Programming'),
('TypeScript', 'Programming'),
('Node.js', 'Backend'),
('Express.js', 'Backend'),
('Django', 'Backend'),
('Flask', 'Backend'),
('Spring', 'Backend'),
('ASP.NET', 'Backend'),
('Android', 'Mobile'),
('iOS', 'Mobile'),
('Flutter', 'Mobile'),
('React Native', 'Mobile'),
('Machine Learning', 'AI/ML'),
('Deep Learning', 'AI/ML'),
('TensorFlow', 'AI/ML'),
('PyTorch', 'AI/ML'),
('Computer Vision', 'AI/ML'),
('NLP', 'AI/ML')
ON CONFLICT (name) DO NOTHING;
