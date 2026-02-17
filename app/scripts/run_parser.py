import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.parser.hh_parser import HeadHunterParser
from app.parser.vacancies_handler import VacanciesHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'parser_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# Уменьшим уровень логирования для некоторых модулей
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска парсера"""
    
    db = SessionLocal()
    
    try:
        logger.info("Запуск парсера вакансий HeadHunter для Владивостока...")
        
        # Инициализируем обработчик и парсер
        handler = VacanciesHandler(db)
        parser = HeadHunterParser()
        
        # Получаем бизнес-роли
        business_roles = handler.get_business_roles()
        
        if not business_roles:
            logger.error("Не найдено бизнес-ролей в базе данных!")
            return
        
        logger.info(f"Найдено бизнес-ролей: {len(business_roles)}")
        for role in business_roles:
            logger.info(f"  - {role['name']} (ID: {role['id']})")
        
        # Ищем вакансии для каждой роли
        vacancies_by_role = parser.search_by_business_roles(business_roles)
        
        total_saved = 0
        total_skipped = 0
        
        # Сохраняем вакансии
        for role_id, vacancies in vacancies_by_role.items():
            if vacancies:
                role_name = next((r['name'] for r in business_roles if r['id'] == role_id), f"ID {role_id}")
                logger.info(f"Сохранение {len(vacancies)} вакансий для роли '{role_name}'...")
                saved, skipped = handler.update_vacancies_for_role(role_id, vacancies)
                total_saved += saved
                total_skipped += skipped
                logger.info(f"  Сохранено: {saved}, Пропущено (дубликаты/ошибки): {skipped}")
            else:
                role_name = next((r['name'] for r in business_roles if r['id'] == role_id), f"ID {role_id}")
                logger.info(f"Для роли '{role_name}' (ID: {role_id}) вакансий не найдено")
        
        # Получаем статистику
        stats = handler.get_vacancies_statistics()
        
        logger.info("=" * 60)
        logger.info("ОТЧЕТ О ВЫПОЛНЕНИИ ПАРСЕРА:")
        logger.info(f"Всего вакансий в базе: {stats['total_vacancies']}")
        logger.info(f"Из них с указанием зарплаты: {stats['total_with_salary']}")
        logger.info(f"Сохранено новых вакансий в этой сессии: {total_saved}")
        logger.info(f"Пропущено (дубликаты/ошибки): {total_skipped}")
        
        if stats['vacancies_by_role']:
            logger.info("Распределение по ролям:")
            for item in stats['vacancies_by_role']:
                logger.info(f"  - {item['role']}: {item['count']} вакансий")
        
        if stats['average_salary']:
            logger.info(f"Средняя зарплата: {stats['average_salary']} руб.")
        
        logger.info("Парсинг завершен успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении парсера: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()