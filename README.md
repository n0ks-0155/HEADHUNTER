# ![Typing SVG](https://readme-typing-svg.herokuapp.com?color=%2336BCF7&lines=HEADHUNTER)
Веб-приложение для сбора и анализа вакансий с HeadHunter.ru в разрезе бизнес-ролей колледжа. Система автоматически обновляет базу вакансий, строит рекомендации для студентов на основе их навыков и предоставляет удобный дашборд для мониторинга бизнес-ролей в базе.
# [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) [![Flask](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/) [![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)](https://www.postgresql.org/) [![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
# Структура проекта
```
ZavalinRabota/
├── app/
│   ├── api/           #Дополнительные API эндпоинты (FastAPI)
│   ├── database/      #Модели, конфигурация, сессия БД
│   ├── parser/        #Парсер HeadHunter и обработчик вакансий
│   ├── services/      #Рекомендации, сервис студентов
│   ├── web/           #Flask-приложение и шаблоны
│   └── scripts/       #Вспомогательные скрипты (инициализация, тесты)
├── .env               #Файл с переменными окружения
├── .gitignore         #Игнорируемые файлы
├── requirements.txt   #Зависимости Python
└── run_app.py         #Точка входа для запуска веб-приложения
```
## Стек
- **Backend**: Python 3.9, Flask, SQLAlchemy, psycopg2
- **Парсинг**: requests, HeadHunter API
- **Рекомендации**: scikit-learn (TF-IDF, cosine similarity), NumPy
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **База данных**: PostgreSQL 16
- **Дополнительно**: python-dotenv, Flask-Bootstrap

## Функциональность
- **Парсер вакансий** – сбор данных с HeadHunter API по 10 бизнес-ролям (Data Analyst, Frontend, Backend, DevOps и др.) для нескольких регионов (Москва, Санкт-Петербург, Новосибирск, Владивосток).
- **Умные рекомендации** – алгоритм, оценивающий соответствие навыков студента требованиям вакансии, с учётом уровня владения, опыта, бизнес-роли и текстовой близости.
- **Веб-интерфейс** – дашборды, списки студентов и вакансий, детальный просмотр рекомендаций.
- **API** – эндпоинты для получения рекомендаций, статистики, управления студентами.
- **Реляционная база данных** – PostgreSQL с полной нормализацией (компании, регионы, навыки, вакансии, студенты).

## Установка и запуск
### 1. Клонирование репозитория
```bash
git clone https://github.com/yourusername/vacancy-monitoring.git
cd vacancy-monitoring
```
### 2. Создание виртуального окружения и установка зависимостей
```bash
python -m venv venv
source venv/bin/activate  #Версия для Linux или macOS
venv\Scripts\activate     #Windows
pip install -r requirements.txt
```
### 3. Настройка переменных окружения
По умолчанию используются учётные данные для тестовой базы, но лучше создать свою:
```env
DB_HOST=your_localhost
DB_PORT=your_port
DB_NAME=your_name
DB_USER=your_user
DB_PASSWORD=your_password
```
### 4. Инициализация базы данных
Создайте схему и таблицы, выполнив скрипт:
```
python app/scripts/init_db.py
```
При необходимости можно наполнить БД шаблонными данными (бизнес-роли, навыки):
```
python app/scripts/insert_students.py
```
### 5. Запуск веб-приложения
```
python run_app.py
```
После чего приложение будет доступно по адресу: *http://localhost:5000*

## Запуск парсера отдельно
Если нужно обновить вакансии без веб-интерфейса:
```
python app/scripts/run_parser.py
```
Для тестового прогона (без записи в БД) можно использовать скрипт *test_parser.py*.

## Рекомендательная система
Алгоритм *recommendation.py* вычисляет оценку для каждой вакансии по формуле:
```
score = 0.4 * skill_match + 0.2 * experience_match + 0.2 * role_match + 0.1 * salary + 0.1 * text_similarity
```
Где: 
- *skill_match* – совпадение навыков с учётом уровня владения.

- *experience_match* – соответствие требуемого опыта.

- *role_match* – близость бизнес-ролей.

- *salary* – Указание зарплаты.

- *text_similarity* – сходство TF‑IDF векторов навыков студента и описания вакансии.

Рекомендации можно получить через API или на странице студента.
