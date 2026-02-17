import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from app.database.models import Vacancy, Skill, BusinessRole, Company, Region, Student
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

class VacanciesHandler:
    """Обработчик для сохранения вакансий в БД с поддержкой справочников"""
    
    def __init__(self, db: Session):
        self.db = db

    
    def get_vacancy_dynamics(self, days: int = 30):
        """Получить количество вакансий по дням за последние N дней"""
        from sqlalchemy import func, cast, Date
        from datetime import datetime, timedelta
        from app.database.models import Vacancy

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Группировка по дате публикации
        results = self.db.query(
            cast(Vacancy.published_at, Date).label('date'),
            func.count(Vacancy.id).label('count')
        ).filter(
            Vacancy.published_at >= start_date,
            Vacancy.published_at <= end_date
        ).group_by(
            cast(Vacancy.published_at, Date)
        ).order_by('date').all()

        # Заполняем все дни в интервале, чтобы не было пропусков
        date_counts = {row.date: row.count for row in results}
        dynamics = []
        current = start_date.date()
        while current <= end_date.date():
            dynamics.append({
                'date': current.isoformat(),
                'count': date_counts.get(current, 0)
            })
            current += timedelta(days=1)

        return dynamics
    
    def get_or_create_company(self, hh_id: int, name: str, url: str = None) -> Company:
        """Получить или создать компанию"""
        if not hh_id:
            # Если нет hh_id, ищем по названию
            company = self.db.query(Company).filter(
                func.lower(Company.name) == func.lower(name)
            ).first()
            
            if company:
                return company
            
            # Создаем новую компанию без hh_id
            company = Company(name=name, url=url)
        else:
            # Ищем по hh_id
            company = self.db.query(Company).filter(Company.hh_id == hh_id).first()
            
            if company:
                # Обновляем название, если оно изменилось
                if company.name != name:
                    company.name = name
                    company.url = url or company.url
                return company
            
            # Создаем новую компанию
            company = Company(hh_id=hh_id, name=name, url=url)
        
        self.db.add(company)
        self.db.flush()  # Сохраняем, чтобы получить ID
        logger.info(f"Создана компания: {name} (HH ID: {hh_id})")
        
        return company
    
    def get_or_create_region(self, hh_id: int, name: str) -> Region:
        """Получить или создать регион"""
        if not hh_id:
            # Если нет hh_id, ищем по названию
            region = self.db.query(Region).filter(
                func.lower(Region.name) == func.lower(name)
            ).first()
            
            if region:
                return region
            
            # Создаем новый регион без hh_id
            region = Region(name=name)
        else:
            # Ищем по hh_id
            region = self.db.query(Region).filter(Region.hh_id == hh_id).first()
            
            if region:
                # Обновляем название, если оно изменилось
                if region.name != name:
                    region.name = name
                return region
            
            # Создаем новый регион
            region = Region(hh_id=hh_id, name=name)
        
        self.db.add(region)
        self.db.flush()  # Сохраняем, чтобы получить ID
        logger.info(f"Создан регион: {name} (HH ID: {hh_id})")
        
        return region
    
    def save_vacancy(self, vacancy_data: Dict) -> Vacancy:
        """Сохранение вакансии в БД"""
        
        # Проверяем, существует ли уже вакансия с таким hh_id
        existing_vacancy = self.db.query(Vacancy).filter(
            Vacancy.hh_id == vacancy_data['hh_id']
        ).first()
        
        if existing_vacancy:
            logger.info(f"Вакансия {vacancy_data['hh_id']} уже существует, пропускаем")
            return existing_vacancy
        
        try:
            # Получаем или создаем компанию
            company = self.get_or_create_company(
                hh_id=vacancy_data.get('company_hh_id'),
                name=vacancy_data.get('company_name', ''),
                url=vacancy_data.get('company_url')
            )
            
            # Получаем или создаем регион
            region = self.get_or_create_region(
                hh_id=vacancy_data.get('region_hh_id'),
                name=vacancy_data.get('region_name', '')
            )
            
            # Создаем новую вакансию
            vacancy = Vacancy(
                hh_id=vacancy_data['hh_id'],
                title=vacancy_data['title'],
                company_id=company.id,
                region_id=region.id,
                salary_from=vacancy_data.get('salary_from'),
                salary_to=vacancy_data.get('salary_to'),
                currency=vacancy_data.get('currency'),
                experience=vacancy_data.get('experience'),
                employment_type=vacancy_data.get('employment_type'),
                schedule=vacancy_data.get('schedule'),
                description=vacancy_data.get('description'),
                key_skills=vacancy_data.get('key_skills'),
                url=vacancy_data.get('url'),
                published_at=vacancy_data.get('published_at'),
                business_role_id=vacancy_data.get('business_role_id')
            )
            
            # Обрабатываем навыки
            self._process_vacancy_skills(vacancy)
            
            self.db.add(vacancy)
            self.db.commit()
            self.db.refresh(vacancy)
            
            logger.info(f"Сохранена вакансия: {vacancy.title} (Компания: {company.name}, Регион: {region.name})")
            
            return vacancy
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при сохранении вакансии {vacancy_data.get('hh_id')}: {e}")
            raise
    
    def _process_vacancy_skills(self, vacancy: Vacancy):
        """Обработка и связывание навыков вакансии"""
        
        if vacancy.key_skills:
            import json
            try:
                skills_list = json.loads(vacancy.key_skills)
                
                for skill_name in skills_list:
                    # Ищем существующий навык или создаем новый
                    skill = self.db.query(Skill).filter(
                        func.lower(Skill.name) == func.lower(skill_name)
                    ).first()
                    
                    if not skill:
                        skill = Skill(name=skill_name)
                        self.db.add(skill)
                        self.db.flush()
                    
                    # Связываем вакансию с навыком
                    if skill not in vacancy.skills:
                        vacancy.skills.append(skill)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга навыков для вакансии: {e}")
            except Exception as e:
                logger.error(f"Ошибка при обработке навыков: {e}")
    
    def get_business_roles(self) -> List[Dict]:
        """Получение списка бизнес-ролей из БД"""
        
        try:
            roles = self.db.query(BusinessRole).all()
            return [{'id': role.id, 'name': role.name} for role in roles]
        except Exception as e:
            logger.error(f"Ошибка при получении бизнес-ролей: {e}")
            return []
    
    def update_vacancies_for_role(self, role_id: int, vacancies_data: List[Dict]):
        """Обновление вакансий для конкретной бизнес-роли"""
        
        saved_count = 0
        skipped_count = 0
        
        for vacancy_data in vacancies_data:
            try:
                # Проверяем обязательные поля
                if not vacancy_data.get('hh_id'):
                    logger.warning("Пропускаем вакансию без hh_id")
                    skipped_count += 1
                    continue
                    
                self.save_vacancy(vacancy_data)
                saved_count += 1
            except Exception as e:
                logger.error(f"Ошибка при сохранении вакансии: {e}")
                skipped_count += 1
        
        return saved_count, skipped_count
    
    def get_vacancies_statistics(self) -> Dict:
        """Получение статистики по вакансиям"""
        
        try:
            # Основная статистика
            total_vacancies = self.db.query(Vacancy).count()
            total_companies = self.db.query(Company).count()
            total_regions = self.db.query(Region).count()
            
            # Вакансии по ролям
            vacancies_by_role = self.db.query(
                BusinessRole.name,
                BusinessRole.id,
                func.count(Vacancy.id).label('count')
            ).outerjoin(Vacancy).group_by(BusinessRole.id, BusinessRole.name).all()
            
            # Средняя зарплата
            avg_salary_result = self.db.query(
                func.avg(
                    (Vacancy.salary_from + Vacancy.salary_to) / 2
                )
            ).filter(
                and_(
                    Vacancy.salary_from.isnot(None), 
                    Vacancy.salary_to.isnot(None)
                )
            ).scalar()
            
            avg_salary = round(float(avg_salary_result)) if avg_salary_result else None
            
            # Дополнительная статистика
            total_with_salary = self.db.query(Vacancy).filter(
                or_(
                    Vacancy.salary_from.isnot(None), 
                    Vacancy.salary_to.isnot(None)
                )
            ).count()
            
            # Топ компаний по количеству вакансий
            top_companies = self.db.query(
                Company.name,
                func.count(Vacancy.id).label('vacancy_count')
            ).join(Vacancy).group_by(Company.id, Company.name).order_by(func.count(Vacancy.id).desc()).limit(5).all()
            
            # Топ регионов по количеству вакансий
            top_regions = self.db.query(
                Region.name,
                func.count(Vacancy.id).label('vacancy_count')
            ).join(Vacancy).group_by(Region.id, Region.name).order_by(func.count(Vacancy.id).desc()).limit(5).all()
            
            return {
                'total_vacancies': total_vacancies,
                'total_companies': total_companies,
                'total_regions': total_regions,
                'total_with_salary': total_with_salary,
                'vacancies_by_role': [
                    {'role': role, 'role_id': role_id, 'count': count} 
                    for role, role_id, count in vacancies_by_role
                ],
                'average_salary': avg_salary,
                'top_companies': [
                    {'company': company, 'vacancy_count': count}
                    for company, count in top_companies
                ],
                'top_regions': [
                    {'region': region, 'vacancy_count': count}
                    for region, count in top_regions
                ]
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {
                'total_vacancies': 0,
                'total_companies': 0,
                'total_regions': 0,
                'total_with_salary': 0,
                'vacancies_by_role': [],
                'average_salary': None,
                'top_companies': [],
                'top_regions': []
            }