import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.parser.hh_parser import HeadHunterParser
from app.parser.vacancies_handler import VacanciesHandler
import logging

# Настройка логирования с детальным уровнем
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_parser():
    """Тестирование парсера без сохранения в БД"""
    
    print("=" * 60)
    print("Тестирование парсера HeadHunter")
    print("=" * 60)
    
    parser = HeadHunterParser()
    
    # Тестовые бизнес-роли
    test_roles = [
        {'id': 1, 'name': 'аналитик данных'},
        {'id': 2, 'name': 'программист'}
    ]
    
    for role in test_roles:
        print(f"\nПоиск вакансий для роли: {role['name']}")
        
        vacancies = parser.search_vacancies(
            search_text=role['name'],
            business_role_id=role['id'],
            per_page=5
        )
        
        print(f"Найдено вакансий: {len(vacancies)}")
        
        if vacancies:
            for i, vacancy in enumerate(vacancies[:3]):  # Покажем первые 3
                print(f"\n{i+1}. {vacancy['title']}")
                print(f"   Компания: {vacancy.get('company', 'Не указана')}")
                if vacancy.get('salary_from') or vacancy.get('salary_to'):
                    print(f"   Зарплата: {vacancy.get('salary_from', '?')} - {vacancy.get('salary_to', '?')} {vacancy.get('currency', '')}")

if __name__ == "__main__":
    test_parser()