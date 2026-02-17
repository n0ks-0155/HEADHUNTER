import numpy as np
import json
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class VacancyRecommender:
    """Система рекомендаций вакансий для студентов"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tfidf_vectorizer = None
        
    def get_student_skills(self, student_id: int) -> List[Dict]:
        """Получить навыки студента с уровнями владения"""
        from app.database.models import Student, Skill, student_skills
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.error(f"Студент с ID {student_id} не найден")
            return []
        
        # Получаем навыки студента с уровнями владения
        skills_query = self.db.query(
            Skill.id,
            Skill.name,
            student_skills.c.proficiency_level
        ).join(
            student_skills, Skill.id == student_skills.c.skill_id
        ).filter(
            student_skills.c.student_id == student_id
        ).all()
        
        return [
            {
                'skill_id': skill_id,
                'skill_name': skill_name,
                'proficiency_level': proficiency_level or 1
            }
            for skill_id, skill_name, proficiency_level in skills_query
        ]
    
    def get_vacancy_skills(self, vacancy_id: int) -> List[str]:
        """Получить навыки вакансии"""
        from app.database.models import Vacancy, Skill, vacancy_skills
        
        vacancy = self.db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        if not vacancy:
            return []
        
        # Пробуем получить навыки из связанной таблицы
        skills_query = self.db.query(
            Skill.name
        ).join(
            vacancy_skills, Skill.id == vacancy_skills.c.skill_id
        ).filter(
            vacancy_skills.c.vacancy_id == vacancy_id
        ).all()
        
        if skills_query:
            return [skill_name for (skill_name,) in skills_query]
        
        # Если нет связей, пытаемся распарсить key_skills
        if vacancy.key_skills:
            try:
                skills_list = json.loads(vacancy.key_skills)
                return [skill for skill in skills_list if isinstance(skill, str)]
            except:
                return []
        
        return []
    
    def calculate_skill_match_score(
        self, 
        student_skills: List[Dict], 
        vacancy_skills: List[str]
    ) -> float:
        """Рассчитать оценку соответствия навыков"""
        
        if not vacancy_skills:
            return 0.0
        
        # Преобразуем навыки студента в словарь {навык: уровень}
        student_skills_dict = {
            skill['skill_name'].lower(): skill['proficiency_level']
            for skill in student_skills
        }
        
        # Считаем совпадения
        matched_skills = []
        skill_scores = []
        
        for vacancy_skill in vacancy_skills:
            vacancy_skill_lower = vacancy_skill.lower()
            
            # Проверяем прямое совпадение
            if vacancy_skill_lower in student_skills_dict:
                matched_skills.append(vacancy_skill)
                # Учитываем уровень владения (от 1 до 5)
                proficiency = student_skills_dict[vacancy_skill_lower]
                skill_scores.append(proficiency / 5.0)  # Нормализуем к 0-1
            else:
                # Проверяем частичные совпадения
                for student_skill in student_skills_dict.keys():
                    if student_skill in vacancy_skill_lower or vacancy_skill_lower in student_skill:
                        matched_skills.append(vacancy_skill)
                        proficiency = student_skills_dict[student_skill]
                        skill_scores.append(proficiency / 10.0)  # Частичное совпадение имеет меньший вес
                        break
        
        # Рассчитываем итоговый score
        if not skill_scores:
            return 0.0
        
        # Средний вес совпадений (0-1)
        avg_match_score = np.mean(skill_scores) if skill_scores else 0
        
        # Доля совпавших навыков
        match_ratio = len(matched_skills) / len(vacancy_skills) if vacancy_skills else 0
        
        # Итоговый score (60% за долю совпадений, 40% за уровень владения)
        final_score = 0.6 * match_ratio + 0.4 * avg_match_score
        
        return round(final_score, 3)
    
    def calculate_salary_score(
        self, 
        student_id: int, 
        vacancy_salary_from: int, 
        vacancy_salary_to: int
    ) -> float:
        """Рассчитать оценку по зарплате"""
        
        # Пока просто проверяем, указана ли зарплата
        if vacancy_salary_from or vacancy_salary_to:
            return 1.0
        return 0.5
    
    def calculate_experience_score(
        self, 
        student_id: int, 
        vacancy_experience: str
    ) -> float:
        """Рассчитать оценку по требуемому опыту"""
        
        # Словарь соответствия опыта к числовому значению
        experience_mapping = {
            'нет опыта': 1,
            'менее года': 2,
            'от 1 года до 3 лет': 3,
            'от 3 до 6 лет': 4,
            'более 6 лет': 5
        }
        
        if not vacancy_experience:
            return 0.7  # Неизвестный опыт
        
        vacancy_exp_level = experience_mapping.get(vacancy_experience.lower(), 3)
        
        # Предположим, что студенты в основном без опыта или с небольшим опытом
        student_exp_level = 2  # "менее года" по умолчанию для студентов
        
        # Оценка: чем меньше разница, тем лучше
        exp_diff = abs(vacancy_exp_level - student_exp_level)
        score = max(0, 1 - (exp_diff / 4))  # Нормализуем к 0-1
        
        return round(score, 2)
    
    def calculate_business_role_score(
        self, 
        student_id: int, 
        vacancy_business_role_id: int
    ) -> float:
        """Рассчитать оценку по соответствию бизнес-роли"""
        
        from app.database.models import Student
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return 0.5
        
        # Если у студента не указана бизнес-роль
        if not student.business_role_id:
            return 0.5
        
        # Полное совпадение ролей
        if student.business_role_id == vacancy_business_role_id:
            return 1.0
        
        # Проверяем родственные роли
        related_roles = {
            1: [3, 9],  # Data Analyst -> Backend Developer, Data Scientist
            2: [3, 4],  # Frontend -> Backend, Fullstack
            3: [1, 2, 4],  # Backend -> Data Analyst, Frontend, Fullstack
            4: [2, 3],  # Fullstack -> Frontend, Backend
            5: [3],  # DevOps -> Backend
            6: [1, 3],  # QA -> Data Analyst, Backend
            7: [],  # Project Manager - особенная роль
            8: [2],  # UX/UI -> Frontend
            9: [1, 3],  # Data Scientist -> Data Analyst, Backend
            10: [3, 5]  # System Admin -> Backend, DevOps
        }
        
        if vacancy_business_role_id in related_roles.get(student.business_role_id, []):
            return 0.7
        
        return 0.3
    
    def calculate_text_similarity(
        self,
        student_id: int,
        vacancy_description: str
    ) -> float:
        """Рассчитать семантическое сходство между навыками студента и описанием вакансии"""
        
        student_skills = self.get_student_skills(student_id)
        if not student_skills or not vacancy_description:
            return 0.5
        
        # Собираем тексты для сравнения
        student_text = " ".join([skill['skill_name'] for skill in student_skills])
        vacancy_text = vacancy_description[:1000]  # Ограничиваем длину
        
        # Используем TF-IDF для векторного представления
        if not self.tfidf_vectorizer:
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='russian')
        
        try:
            # Создаем корпус из двух текстов
            corpus = [student_text, vacancy_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Вычисляем косинусное сходство
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return round(float(similarity), 3)
        except:
            # В случае ошибки возвращаем среднее значение
            return 0.5
    
    def calculate_final_score(
        self,
        skill_score: float,
        salary_score: float,
        experience_score: float,
        role_score: float,
        text_similarity: float
    ) -> float:
        """Рассчитать итоговый рейтинг рекомендации"""
        
        # Веса компонентов
        weights = {
            'skill': 0.4,      # Навыки - самый важный фактор
            'salary': 0.1,     # Зарплата
            'experience': 0.2, # Опыт
            'role': 0.2,       # Бизнес-роль
            'text': 0.1        # Текстовая схожесть
        }
        
        final_score = (
            skill_score * weights['skill'] +
            salary_score * weights['salary'] +
            experience_score * weights['experience'] +
            role_score * weights['role'] +
            text_similarity * weights['text']
        )
        
        return round(final_score, 3)
    
    def _get_matched_skills(
        self, 
        student_skills: List[Dict], 
        vacancy_skills: List[str]
    ) -> List[str]:
        """Получить список совпавших навыков"""
        
        if not student_skills or not vacancy_skills:
            return []
        
        student_skill_names = {skill['skill_name'].lower() for skill in student_skills}
        matched = []
        
        for vacancy_skill in vacancy_skills:
            vacancy_skill_lower = vacancy_skill.lower()
            
            if vacancy_skill_lower in student_skill_names:
                matched.append(vacancy_skill)
            else:
                # Проверяем частичные совпадения
                for student_skill in student_skill_names:
                    if student_skill in vacancy_skill_lower or vacancy_skill_lower in student_skill:
                        matched.append(f"{vacancy_skill} (~{student_skill})")
                        break
        
        return matched
    
    def recommend_vacancies_for_student(
        self, 
        student_id: int, 
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Dict]:
        """Рекомендовать вакансии для студента"""
        
        from app.database.models import Vacancy, Company, Region, BusinessRole, Student
        
        logger.info(f"Поиск рекомендаций для студента ID {student_id}")
        
        # Получаем студента
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.error(f"Студент с ID {student_id} не найден")
            return []
        
        # Получаем навыки студента
        student_skills = self.get_student_skills(student_id)
        if not student_skills:
            logger.warning(f"У студента {student_id} не указаны навыки")
        
        # Получаем все активные вакансии (за последние 30 дней)
        # Используем правильный синтаксис для PostgreSQL интервала
        thirty_days_ago = func.now() - text("interval '30 days'")
        
        vacancies_query = self.db.query(
            Vacancy,
            Company.name.label('company_name'),
            Region.name.label('region_name'),
            BusinessRole.name.label('business_role_name')
        ).join(
            Company, Vacancy.company_id == Company.id
        ).join(
            Region, Vacancy.region_id == Region.id
        ).join(
            BusinessRole, Vacancy.business_role_id == BusinessRole.id
        ).filter(
            Vacancy.published_at >= thirty_days_ago
        ).order_by(
            Vacancy.published_at.desc()
        ).limit(100)  # Ограничиваем для производительности
        
        recommendations = []
        
        for vacancy, company_name, region_name, business_role_name in vacancies_query.all():
            # Получаем навыки вакансии
            vacancy_skills = self.get_vacancy_skills(vacancy.id)
            
            # Рассчитываем отдельные оценки
            skill_score = self.calculate_skill_match_score(student_skills, vacancy_skills)
            salary_score = self.calculate_salary_score(student_id, vacancy.salary_from, vacancy.salary_to)
            experience_score = self.calculate_experience_score(student_id, vacancy.experience)
            role_score = self.calculate_business_role_score(student_id, vacancy.business_role_id)
            text_similarity = self.calculate_text_similarity(student_id, vacancy.description)
            
            # Рассчитываем итоговый score
            final_score = self.calculate_final_score(
                skill_score, salary_score, experience_score, 
                role_score, text_similarity
            )
            
            # Фильтруем по минимальному score
            if final_score >= min_score:
                recommendation = {
                    'vacancy_id': vacancy.id,
                    'hh_id': vacancy.hh_id,
                    'title': vacancy.title,
                    'company_name': company_name,
                    'region_name': region_name,
                    'business_role_name': business_role_name,
                    'salary_from': vacancy.salary_from,
                    'salary_to': vacancy.salary_to,
                    'currency': vacancy.currency,
                    'experience': vacancy.experience,
                    'url': vacancy.url,
                    'published_at': vacancy.published_at,
                    'scores': {
                        'final_score': final_score,
                        'skill_score': skill_score,
                        'salary_score': salary_score,
                        'experience_score': experience_score,
                        'role_score': role_score,
                        'text_similarity': text_similarity
                    },
                    'matched_skills': self._get_matched_skills(student_skills, vacancy_skills),
                    'total_vacancy_skills': len(vacancy_skills)
                }
                recommendations.append(recommendation)
        
        # Сортируем по итоговому score
        recommendations.sort(key=lambda x: x['scores']['final_score'], reverse=True)
        
        # Ограничиваем количество
        recommendations = recommendations[:limit]
        
        logger.info(f"Найдено {len(recommendations)} рекомендаций для студента {student_id}")
        
        return recommendations
    
    def recommend_vacancies_by_business_role(
        self, 
        business_role_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Рекомендовать вакансии по бизнес-роли (без учета конкретного студента)"""
        
        from app.database.models import Vacancy, Company, Region, BusinessRole
        
        vacancies_query = self.db.query(
            Vacancy,
            Company.name.label('company_name'),
            Region.name.label('region_name'),
            BusinessRole.name.label('business_role_name')
        ).join(
            Company, Vacancy.company_id == Company.id
        ).join(
            Region, Vacancy.region_id == Region.id
        ).join(
            BusinessRole, Vacancy.business_role_id == BusinessRole.id
        ).filter(
            Vacancy.business_role_id == business_role_id,
            Vacancy.published_at >= func.now() - text("interval '30 days'")
        ).order_by(
            Vacancy.published_at.desc()
        ).limit(limit)
        
        vacancies = []
        for vacancy, company_name, region_name, business_role_name in vacancies_query.all():
            vacancies.append({
                'vacancy_id': vacancy.id,
                'title': vacancy.title,
                'company_name': company_name,
                'region_name': region_name,
                'business_role_name': business_role_name,
                'salary_from': vacancy.salary_from,
                'salary_to': vacancy.salary_to,
                'currency': vacancy.currency,
                'experience': vacancy.experience,
                'url': vacancy.url,
                'published_at': vacancy.published_at,
                'key_skills': json.loads(vacancy.key_skills) if vacancy.key_skills else []
            })
        
        return vacancies
    
    def get_recommendation_stats(self, student_id: int) -> Dict:
        """Получить статистику рекомендаций для студента"""
        
        from app.database.models import Student
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {}
        
        # Получаем рекомендации
        recommendations = self.recommend_vacancies_for_student(student_id, limit=50)
        
        if not recommendations:
            return {
                'student_id': student_id,
                'student_name': student.name,
                'total_recommendations': 0,
                'stats': {}
            }
        
        # Анализируем рекомендации
        scores = [rec['scores']['final_score'] for rec in recommendations]
        skill_scores = [rec['scores']['skill_score'] for rec in recommendations]
        
        # Группируем по бизнес-ролям
        role_distribution = {}
        for rec in recommendations:
            role = rec['business_role_name']
            role_distribution[role] = role_distribution.get(role, 0) + 1
        
        # Группируем по компаниям
        company_distribution = {}
        for rec in recommendations:
            company = rec['company_name']
            company_distribution[company] = company_distribution.get(company, 0) + 1
        
        return {
            'student_id': student_id,
            'student_name': student.name,
            'total_recommendations': len(recommendations),
            'stats': {
                'avg_score': round(np.mean(scores), 3) if scores else 0,
                'max_score': round(max(scores), 3) if scores else 0,
                'min_score': round(min(scores), 3) if scores else 0,
                'avg_skill_score': round(np.mean(skill_scores), 3) if skill_scores else 0,
                'role_distribution': role_distribution,
                'top_companies': dict(sorted(company_distribution.items(), 
                                           key=lambda x: x[1], reverse=True)[:5])
            }
        }
