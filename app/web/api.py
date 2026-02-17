from flask import Blueprint, jsonify, request
from app.database.session import SessionLocal
from app.services.student_service import StudentService
import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/student_count')
def student_count():
    """API для получения количества студентов"""
    db = SessionLocal()
    try:
        from app.database.models import Student
        count = db.query(Student).count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        db.close()

@api_bp.route('/api/recommendation_stats')
def recommendation_stats():
    """API для получения статистики рекомендаций"""
    db = SessionLocal()
    try:
        from app.database.models import Student
        student_service = StudentService(db)
        students = student_service.get_all_students()
        
        total_recommendations = 0
        students_with_recommendations = 0
        total_score = 0
        
        # Для каждого студента получаем рекомендации
        from app.services.recommendation import VacancyRecommender
        recommender = VacancyRecommender(db)
        
        for student in students:
            recommendations = recommender.recommend_vacancies_for_student(
                student_id=student['id'],
                limit=10,
                min_score=0.1
            )
            
            if recommendations:
                students_with_recommendations += 1
                total_recommendations += len(recommendations)
                
                for rec in recommendations:
                    total_score += rec['scores']['final_score']
        
        avg_score = total_score / total_recommendations if total_recommendations > 0 else 0
        
        return jsonify({
            'stats': {
                'total_recommendations': total_recommendations,
                'students_with_recommendations': students_with_recommendations,
                'avg_score': avg_score
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        db.close()

@api_bp.route('/api/vacancy/<int:vacancy_id>')
def get_vacancy_details(vacancy_id):
    """API для получения детальной информации о вакансии"""
    db = SessionLocal()
    try:
        from app.database.models import Vacancy, Company, Region, BusinessRole
        
        vacancy = db.query(
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
        ).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            return jsonify({'error': 'Вакансия не найдена'})
        
        vacancy_obj, company_name, region_name, business_role_name = vacancy
        
        return jsonify({
            'id': vacancy_obj.id,
            'hh_id': vacancy_obj.hh_id,
            'title': vacancy_obj.title,
            'company_name': company_name,
            'region_name': region_name,
            'business_role_name': business_role_name,
            'salary_from': vacancy_obj.salary_from,
            'salary_to': vacancy_obj.salary_to,
            'currency': vacancy_obj.currency,
            'experience': vacancy_obj.experience,
            'employment_type': vacancy_obj.employment_type,
            'schedule': vacancy_obj.schedule,
            'description': vacancy_obj.description,
            'url': vacancy_obj.url,
            'published_at': vacancy_obj.published_at.isoformat() if vacancy_obj.published_at else None,
            'created_at': vacancy_obj.created_at.isoformat() if vacancy_obj.created_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        db.close()

@api_bp.route('/api/parser_history')
def parser_history():
    """API для получения истории запусков парсера"""
    # В реальной системе здесь нужно получать данные из базы
    # Для демонстрации возвращаем фиктивные данные
    return jsonify({
        'history': [
            {
                'timestamp': (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
                'vacancies_added': 45,
                'success': True
            },
            {
                'timestamp': (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat(),
                'vacancies_added': 38,
                'success': True
            },
            {
                'timestamp': (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
                'vacancies_added': 0,
                'success': False
            }
        ]
    })

@api_bp.route('/api/test_data', methods=['POST'])
def create_test_student():
    """API для создания тестового студента"""
    db = SessionLocal()
    try:
        student_service = StudentService(db)
        
        # Создаем тестового студента
        from app.database.models import Skill
        import random
        
        # Находим случайные навыки
        skills = db.query(Skill).limit(5).all()
        skill_data = [{'skill_id': s.id, 'proficiency_level': random.randint(2, 5)} for s in skills]
        
        student = student_service.create_student(
            name='Тестовый Студент ' + str(random.randint(100, 999)),
            email=f'test.student{random.randint(1000, 9999)}@example.com',
            business_role_id=random.randint(1, 10),
            skills=skill_data
        )
        
        if 'error' in student:
            return jsonify({'success': False, 'error': student['error']})
        
        return jsonify({'success': True, 'student_id': student['id']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db.close()
