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
