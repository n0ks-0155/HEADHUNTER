# app/web/app.py
"""
Главное приложение Flask для демонстрации системы мониторинга вакансий
"""

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from flask_bootstrap import Bootstrap
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.session import SessionLocal
from app.services.recommendation import VacancyRecommender
from app.services.student_service import StudentService
from app.parser.vacancies_handler import VacanciesHandler
from app.parser.hh_parser import HeadHunterParser

app = Flask(__name__)
app.secret_key = 'dev-secret-key-2024-vacancy-monitoring'
Bootstrap(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.context_processor
def inject_db_stats():
    """Контекстный процессор для добавления статистики базы данных в шаблоны"""
    def get_db_stats():
        db = SessionLocal()
        try:
            handler = VacanciesHandler(db)
            stats = handler.get_vacancies_statistics()
            return stats
        except Exception as e:
            logger.error(f"Ошибка при получении статистики БД: {e}")
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
        finally:
            db.close()
    
    return dict(get_db_stats=get_db_stats)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/vacancy_dynamics')
def vacancy_dynamics():
    """API для получения динамики вакансий по дням"""
    db = SessionLocal()
    try:
        handler = VacanciesHandler(db)
        days = request.args.get('days', default=30, type=int)
        dynamics = handler.get_vacancy_dynamics(days)
        return jsonify(dynamics)
    except Exception as e:
        logger.error(f"Ошибка получения динамики: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/dashboard')
def dashboard():
    """Дашборд со статистикой"""
    db = SessionLocal()
    try:
        handler = VacanciesHandler(db)
        stats = handler.get_vacancies_statistics()
        
        return render_template('dashboard.html', 
                             stats=stats,
                             total_vacancies=stats['total_vacancies'],
                             total_companies=stats['total_companies'],
                             total_regions=stats['total_regions'],
                             average_salary=stats['average_salary'])
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        return render_template('dashboard.html', error=str(e))
    finally:
        db.close()

@app.route('/students')
def students():
    """Страница со списком студентов"""
    db = SessionLocal()
    try:
        student_service = StudentService(db)
        students_list = student_service.get_all_students()
        
        return render_template('students.html', students=students_list)
    except Exception as e:
        logger.error(f"Ошибка при получении студентов: {e}")
        return render_template('students.html', error=str(e))
    finally:
        db.close()

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    """Детальная страница студента с рекомендациями"""
    db = SessionLocal()
    try:
        student_service = StudentService(db)
        recommender = VacancyRecommender(db)
        
        # Получаем профиль студента
        profile = student_service.get_student_profile(student_id)
        if not profile:
            flash(f'Студент с ID {student_id} не найден', 'danger')
            return redirect(url_for('students'))
        
        # Получаем рекомендации
        recommendations = recommender.recommend_vacancies_for_student(
            student_id=student_id,
            limit=10,
            min_score=0.3
        )
        
        return render_template('student_detail.html', 
                             student=profile,
                             recommendations=recommendations)
    except Exception as e:
        logger.error(f"Ошибка при получении данных студента: {e}")
        flash(f'Ошибка при получении данных студента: {e}', 'danger')
        return redirect(url_for('students'))
    finally:
        db.close()

@app.route('/vacancies')
def vacancies():
    """Страница со списком вакансий"""
    db = SessionLocal()
    try:
        from app.database.models import Vacancy, Company, Region, BusinessRole
        
        vacancies_list = db.query(
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
        ).order_by(Vacancy.published_at.desc()).limit(100).all()
        
        return render_template('vacancies.html', vacancies=vacancies_list)
    except Exception as e:
        logger.error(f"Ошибка при получении вакансий: {e}")
        return render_template('vacancies.html', error=str(e))
    finally:
        db.close()

@app.route('/parser')
def parser_page():
    """Страница парсера"""
    return render_template('parser.html')

@app.route('/api/run_parser', methods=['POST'])
def run_parser():
    """API для запуска парсера"""
    try:
        # Создаем логгер для отслеживания прогресса
        logger.info("Запуск парсера...")
        
        db = SessionLocal()
        handler = VacanciesHandler(db)
        parser = HeadHunterParser()
        
        # Получаем бизнес-роли
        business_roles = handler.get_business_roles()
        
        if not business_roles:
            return jsonify({'success': False, 'error': 'Нет бизнес-ролей в базе'})
        
        # Ищем вакансии для каждой роли
        # Список регионов: 1 - Москва, 2 - Санкт-Петербург, 76 - Новосибирск, 22 - Владивосток
        area_ids = [1, 2, 76, 22]
        vacancies_by_role = parser.search_by_business_roles(business_roles, area_ids=area_ids)
        
        total_saved = 0
        total_skipped = 0
        
        for role_id, vacancies in vacancies_by_role.items():
            if vacancies:
                saved, skipped = handler.update_vacancies_for_role(role_id, vacancies)
                total_saved += saved
                total_skipped += skipped
        
        # Получаем обновленную статистику
        stats = handler.get_vacancies_statistics()
        
        return jsonify({
            'success': True,
            'message': f'Парсер успешно выполнен. Сохранено новых вакансий: {total_saved}, пропущено: {total_skipped}',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Ошибка при запуске парсера: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test_parser', methods=['POST'])
def test_parser():
    """Тестовый запуск парсера без сохранения в БД"""
    try:
        db = SessionLocal()
        handler = VacanciesHandler(db)
        parser = HeadHunterParser()

        # Получаем бизнес-роли
        business_roles = handler.get_business_roles()
        if not business_roles:
            return jsonify({'success': False, 'error': 'Нет бизнес-ролей в базе'})

        # Список регионов: Москва (1), СПб (2), Новосибирск (76), Владивосток (22)
        area_ids = [1, 2, 76, 22]

        # Запускаем парсер (метод уже поддерживает несколько регионов)
        vacancies_by_role = parser.search_by_business_roles(business_roles, area_ids=area_ids)

        # Формируем статистику для отчёта (без сохранения)
        stats = {}
        total_found = 0
        for role in business_roles:
            role_id = role['id']
            vacancies = vacancies_by_role.get(role_id, [])
            # Убираем дубликаты (на всякий случай, хотя метод уже возвращает уникальные)
            unique = {v['hh_id']: v for v in vacancies if v.get('hh_id')}.values()
            vacancies_list = list(unique)
            count = len(vacancies_list)
            total_found += count
            # Берём первые 3 названия для примера
            examples = [v['title'] for v in vacancies_list[:3]]
            stats[role['name']] = {
                'count': count,
                'examples': examples
            }

        return jsonify({
            'success': True,
            'total_found': total_found,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Ошибка при тестовом запуске парсера: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db.close()

@app.route('/api/statistics')
def get_statistics():
    """API для получения статистики"""
    db = SessionLocal()
    try:
        handler = VacanciesHandler(db)
        stats = handler.get_vacancies_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        db.close()

@app.route('/api/student/<int:student_id>/recommendations')
def get_student_recommendations(student_id):
    """API для получения рекомендаций студента"""
    db = SessionLocal()
    try:
        recommender = VacancyRecommender(db)
        recommendations = recommender.recommend_vacancies_for_student(
            student_id=student_id,
            limit=20,
            min_score=0.2
        )
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        db.close()

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    """Страница добавления нового студента"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        business_role_id = request.form.get('business_role_id')
        skills_text = request.form.get('skills')
        
        db = SessionLocal()
        try:
            student_service = StudentService(db)
            
            # Преобразуем навыки из текста в список
            skills = []
            if skills_text:
                skill_names = [s.strip() for s in skills_text.split(',')]
                from app.database.models import Skill
                for skill_name in skill_names:
                    skill = db.query(Skill).filter(Skill.name == skill_name).first()
                    if skill:
                        skills.append({'skill_id': skill.id, 'proficiency_level': 3})
            
            student = student_service.create_student(
                name=name,
                email=email,
                business_role_id=int(business_role_id) if business_role_id else None,
                skills=skills
            )
            
            if 'error' in student:
                flash(f'Ошибка: {student["error"]}', 'danger')
            else:
                flash(f'Студент {name} успешно добавлен!', 'success')
                return redirect(url_for('student_detail', student_id=student['id']))
                
        except Exception as e:
            flash(f'Ошибка при добавлении студента: {e}', 'danger')
        finally:
            db.close()
    
    # GET запрос - показываем форму
    db = SessionLocal()
    try:
        from app.database.models import BusinessRole, Skill
        business_roles = db.query(BusinessRole).all()
        skills = db.query(Skill).all()
        return render_template('add_student.html', 
                             business_roles=business_roles,
                             skills=skills)
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
