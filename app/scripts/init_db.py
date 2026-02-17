import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import engine, Base, create_schema_if_not_exists
from app.database.models import BusinessRole, Skill, Company, Region, Student, Vacancy
from app.database.session import SessionLocal
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Создание таблиц в базе данных"""
    try:
        # Создаем схему, если ее нет
        create_schema_if_not_exists()
        
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы успешно созданы в схеме 'msod7'")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        raise

def seed_initial_data():
    """Заполнение начальными данными"""
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже данные
        existing_roles = db.query(BusinessRole).count()
        if existing_roles > 0:
            logger.info("Данные уже существуют, пропускаем заполнение")
            return
        
        # Бизнес-роли колледжа
        business_roles = [
            BusinessRole(
                name="Data Analyst",
                description="Аналитик данных, работа с BI-системами"
            ),
            BusinessRole(
                name="Frontend Developer",
                description="Разработка пользовательских интерфейсов"
            ),
            BusinessRole(
                name="Backend Developer",
                description="Разработка серверной части приложений"
            ),
            BusinessRole(
                name="Fullstack Developer",
                description="Полный цикл разработки приложений"
            ),
            BusinessRole(
                name="DevOps Engineer",
                description="Автоматизация процессов разработки и развертывания"
            ),
            BusinessRole(
                name="QA Engineer",
                description="Тестирование и обеспечение качества ПО"
            ),
            BusinessRole(
                name="Project Manager",
                description="Управление проектами и командами разработки"
            ),
            BusinessRole(
                name="UX/UI Designer",
                description="Дизайн пользовательских интерфейсов"
            ),
        ]
        
        for role in business_roles:
            db.add(role)
        
        # Навыки
        skills = [
            Skill(name="Python", category="Programming"),
            Skill(name="JavaScript", category="Programming"),
            Skill(name="SQL", category="Database"),
            Skill(name="HTML/CSS", category="Web"),
            Skill(name="React", category="Frontend"),
            Skill(name="Vue.js", category="Frontend"),
            Skill(name="Docker", category="DevOps"),
            Skill(name="Git", category="Tools"),
            Skill(name="PostgreSQL", category="Database"),
            Skill(name="MongoDB", category="Database"),
            Skill(name="Linux", category="Systems"),
            Skill(name="AWS", category="Cloud"),
            Skill(name="Agile", category="Methodology"),
            Skill(name="Scrum", category="Methodology"),
            Skill(name="Figma", category="Design"),
            Skill(name="Tableau", category="Analytics"),
            Skill(name="Power BI", category="Analytics"),
            Skill(name="Kubernetes", category="DevOps"),
            Skill(name="Java", category="Programming"),
            Skill(name="C#", category="Programming"),
        ]
        
        for skill in skills:
            db.add(skill)
        
        # Регионы
        regions = [
            Region(hh_id=113, name="Россия"),
            Region(hh_id=1, name="Москва"),
            Region(hh_id=2, name="Санкт-Петербург"),
            Region(hh_id=22, name="Владивосток"),
            Region(hh_id=76, name="Новосибирск"),
            Region(hh_id=66, name="Екатеринбург"),
        ]
        
        for region in regions:
            db.add(region)
        
        # Тестовые компании
        test_companies = [
            Company(name="Яндекс", hh_id=1740, url="https://yandex.ru"),
            Company(name="Сбер", hh_id=3529, url="https://sber.ru"),
            Company(name="Тинькофф", hh_id=78638, url="https://tinkoff.ru"),
            Company(name="VK", hh_id=15478, url="https://vk.com"),
            Company(name="Озон", hh_id=2180, url="https://ozon.ru"),
        ]
        
        for company in test_companies:
            db.add(company)
        
        # Тестовые студенты
        students = [
            Student(
                name="Иванов Иван",
                email="ivanov@example.com",
                business_role_id=1  # Data Analyst
            ),
            Student(
                name="Петров Петр",
                email="petrov@example.com",
                business_role_id=2  # Frontend Developer
            ),
        ]
        
        for student in students:
            db.add(student)
        
        db.commit()
        logger.info("Начальные данные успешно добавлены")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при заполнении данных: {e}")
        raise
    finally:
        db.close()

def check_database():
    """Проверка структуры базы данных"""
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 60)
        print("ПРОВЕРКА СТРУКТУРЫ БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        # Проверяем наличие таблиц
        tables = ['companies', 'regions', 'business_roles', 'skills', 'vacancies', 'students', 'vacancy_skills', 'student_skills']
        
        for table in tables:
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM msod7.{table}")).scalar()
                print(f"✓ Таблица '{table}': {count} записей")
            except Exception as e:
                print(f"✗ Таблица '{table}': ОШИБКА - {e}")
        
        print("\n" + "=" * 60)
        print("СТАТИСТИКА:")
        print("=" * 60)
        
        # Статистика
        stats_queries = [
            ("Компании", "SELECT COUNT(*) FROM msod7.companies"),
            ("Регионы", "SELECT COUNT(*) FROM msod7.regions"),
            ("Бизнес-роли", "SELECT COUNT(*) FROM msod7.business_roles"),
            ("Навыки", "SELECT COUNT(*) FROM msod7.skills"),
            ("Вакансии", "SELECT COUNT(*) FROM msod7.vacancies"),
            ("Студенты", "SELECT COUNT(*) FROM msod7.students"),
        ]
        
        for name, query in stats_queries:
            count = db.execute(text(query)).scalar()
            print(f"{name}: {count}")
        
    except Exception as e:
        print(f"Ошибка при проверке базы данных: {e}")
    finally:
        db.close()

def run_sql_file(filename):
    """Выполнить SQL файл"""
    db = SessionLocal()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Разделяем SQL на отдельные команды
        commands = sql_content.split(';')
        
        for command in commands:
            command = command.strip()
            if command:
                try:
                    db.execute(text(command))
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"Ошибка при выполнении команды: {e}")
                    print(f"Команда: {command[:100]}...")
        
        print(f"✅ SQL файл {filename} выполнен успешно")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении SQL файла: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Инициализация обновленной базы данных v2.0 (исправленная)...")
    print("-" * 60)
    
    print("Создание таблиц через SQLAlchemy...")
    create_tables()
    
    # Заполняем начальными данными
    print("Заполнение начальными данными...")
    seed_initial_data()
    
    # Проверяем базу данных
    check_database()
    
    print("\n" + "=" * 60)
    print("База данных успешно инициализирована!")
    print("=" * 60)
