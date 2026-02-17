import requests
import time
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HeadHunterParser:
    """Парсер вакансий с HeadHunter API с поддержкой справочников компаний и регионов"""
    
    BASE_URL = "https://api.hh.ru/vacancies"
    AREAS_URL = "https://api.hh.ru/areas"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VacancyMonitoringSystem/1.0 (4t3w35g@gmail.com)',
            'HH-User-Agent': 'VacancyMonitoringSystem/1.0 (4t3w35g@gmail.com)',
            'Accept': 'application/json'
        })
    
    def get_area_id(self, area_name: str) -> Optional[int]:
        """Получение ID региона по названию (кешируем для скорости)"""
        # Кеш регионов
        if not hasattr(self, '_areas_cache'):
            self._areas_cache = {}
            try:
                response = self.session.get(self.AREAS_URL, timeout=10)
                if response.status_code == 200:
                    areas = response.json()
                    # Рекурсивно собираем все регионы
                    def collect_areas(areas_list):
                        for area in areas_list:
                            self._areas_cache[area['name'].lower()] = area['id']
                            if area.get('areas'):
                                collect_areas(area['areas'])
                    collect_areas(areas)
            except Exception as e:
                logger.error(f"Ошибка при получении регионов: {e}")
        
        return self._areas_cache.get(area_name.lower())
    
    def search_vacancies(self, search_text: str, business_role_id: int, 
                        area: int = 22,  # 22 - Владивосток по умолчанию
                        per_page: int = 20,
                        page_limit: int = 1) -> List[Dict]:
        """Поиск вакансий по ключевым словам"""
        
        params = {
            'text': search_text,
            'area': area,
            'per_page': per_page,
            'page': 0
        }
        
        all_vacancies = []
        
        try:
            for page in range(0, page_limit):
                params['page'] = page
                
                logger.info(f"Запрос страницы {page + 1} для '{search_text}' (регион ID: {area})")
                
                response = self.session.get(self.BASE_URL, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"Ошибка HTTP {response.status_code}: {response.text[:100]}")
                    if response.status_code == 400:
                        # Пробуем без параметров, которые могут вызывать проблемы
                        params_copy = params.copy()
                        response = self.session.get(self.BASE_URL, params=params_copy)
                        
                        if response.status_code != 200:
                            logger.error(f"Повторный запрос также завершился с ошибкой {response.status_code}")
                            break
                    else:
                        break
                
                data = response.json()
                
                vacancies = data.get('items', [])
                logger.info(f"Получено {len(vacancies)} вакансий на странице {page + 1}")
                
                for vacancy in vacancies:
                    # Получаем детальную информацию о вакансии
                    vacancy_details = self.get_vacancy_details(vacancy['id'])
                    if vacancy_details:
                        # Добавляем ID бизнес-роли
                        vacancy_details['business_role_id'] = business_role_id
                        all_vacancies.append(vacancy_details)
                    else:
                        logger.warning(f"Не удалось получить детали вакансии {vacancy.get('id')}")
                
                # Если вакансий нет или это последняя страница, выходим
                pages = data.get('pages', 0)
                if not vacancies or page >= pages - 1 or page >= page_limit - 1:
                    break
                    
                time.sleep(0.5)  # Задержка между запросами
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к API HH: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
        
        return all_vacancies
    
    def get_vacancy_details(self, vacancy_id: int) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""
        
        try:
            url = f"{self.BASE_URL}/{vacancy_id}"
            
            response = self.session.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Вакансия {vacancy_id} недоступна: {response.status_code}")
                return None
                
            data = response.json()
            
            # Получаем данные компании
            company_data = data.get('employer', {})
            company_id = company_data.get('id') if isinstance(company_data, dict) else None
            company_name = company_data.get('name', '') if isinstance(company_data, dict) else str(company_data)
            company_url = company_data.get('alternate_url', '') if isinstance(company_data, dict) else ''
            
            # Получаем данные региона
            region_data = data.get('area', {})
            region_id = region_data.get('id') if isinstance(region_data, dict) else None
            region_name = region_data.get('name', '') if isinstance(region_data, dict) else ''
            
            # Парсим зарплату
            salary = data.get('salary')
            salary_from = salary.get('from') if salary else None
            salary_to = salary.get('to') if salary else None
            currency = salary.get('currency') if salary else None
            
            # Парсим навыки
            key_skills = [skill['name'] for skill in data.get('key_skills', [])]
            
            # Парсим дату публикации
            published_at = None
            if data.get('published_at'):
                try:
                    # Убираем микросекунды, если они есть
                    published_str = data['published_at'].split('.')[0] if '.' in data['published_at'] else data['published_at']
                    published_at = datetime.strptime(published_str, '%Y-%m-%dT%H:%M:%S%z')
                except ValueError as e:
                    logger.warning(f"Неверный формат даты {data['published_at']}: {e}")
            
            vacancy_data = {
                'hh_id': int(vacancy_id) if vacancy_id else None,
                'title': data.get('name', ''),
                'company_hh_id': company_id,
                'company_name': company_name,
                'company_url': company_url,
                'region_hh_id': region_id,
                'region_name': region_name,
                'salary_from': salary_from,
                'salary_to': salary_to,
                'currency': currency,
                'experience': data.get('experience', {}).get('name', '') if isinstance(data.get('experience'), dict) else '',
                'employment_type': data.get('employment', {}).get('name', '') if isinstance(data.get('employment'), dict) else '',
                'schedule': data.get('schedule', {}).get('name', '') if isinstance(data.get('schedule'), dict) else '',
                'description': self._clean_description(data.get('description', '')),
                'key_skills': json.dumps(key_skills, ensure_ascii=False),
                'url': data.get('alternate_url', f'https://hh.ru/vacancy/{vacancy_id}'),
                'published_at': published_at
            }
            
            return vacancy_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении деталей вакансии {vacancy_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке вакансии {vacancy_id}: {e}")
            return None
    
    def _clean_description(self, description: str) -> str:
        """Очистка описания от HTML-тегов"""
        if not description:
            return ""
        
        # Простая очистка HTML-тегов
        import re
        clean = re.sub(r'<[^>]+>', ' ', description)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:5000]  # Ограничиваем длину
    
    def search_by_business_roles(self, business_roles: List[Dict], area_ids: List[int] = None) -> Dict[int, List[Dict]]:
        """Поиск вакансий для списка бизнес-ролей по нескольким регионам"""
        if area_ids is None:
            area_ids = [22]  # по умолчанию Владивосток

        # Словарь для русскоязычных поисковых запросов
        russian_queries = {
            "Data Analyst": "аналитик данных",
            "Frontend Developer": "frontend разработчик OR фронтенд разработчик",
            "Backend Developer": "backend разработчик OR бэкенд разработчик",
            "Fullstack Developer": "fullstack разработчик OR фулстек разработчик",
            "DevOps Engineer": "devops инженер OR девопс инженер",
            "QA Engineer": "qa инженер OR тестировщик",
            "Project Manager": "project manager OR менеджер проектов",
            "UX/UI Designer": "ui ux дизайнер OR дизайнер интерфейсов",
            "Data Scientist": "data scientist OR специалист по данным",
            "System Administrator": "системный администратор"
        }

        results = {role['id']: [] for role in business_roles}

        for role in business_roles:
            role_name = role['name']
            search_text = russian_queries.get(role_name, role_name)

            for area_id in area_ids:
                logger.info(f"Поиск вакансий для роли: {role_name} (регион ID: {area_id})")
                vacancies = self.search_vacancies(
                    search_text=search_text,
                    business_role_id=role['id'],
                    area=area_id,
                    per_page=10,
                    page_limit=2
                )
                results[role['id']].extend(vacancies)
                time.sleep(0.5)  # задержка между регионами

            # Удаляем дубликаты внутри одной роли (по hh_id)
            unique = {}
            for vac in results[role['id']]:
                hh_id = vac.get('hh_id')
                if hh_id and hh_id not in unique:
                    unique[hh_id] = vac
            results[role['id']] = list(unique.values())

            logger.info(f"Найдено уникальных вакансий для роли {role_name}: {len(results[role['id']])}")
            time.sleep(1)  # задержка между ролями

        return results
