# scripts/test_recommendation_fixed.py

#!/usr/bin/env python3
"""
Исправленный скрипт для тестирования алгоритма рекомендаций
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.services.recommendation import VacancyRecommender
from app.services.student_service import StudentService

def test_recommendations_for_all_students():
    """Тестирование системы рекомендаций для всех студентов"""
    
    db = SessionLocal()
    
    try:
        # Создаем сервисы
        recommender = VacancyRecommender(db)
        student_service = StudentService(db)
        
        # 1. Проверяем, есть ли студенты в базе
        print("=" * 80)
        print("ТЕСТИРОВАНИЕ СИСТЕМЫ РЕКОМЕНДАЦИЙ")
        print("=" * 80)
        
        students = student_service.get_all_students()
        
        if not students:
            print("\n1. ПРОВЕРКА СТУДЕНТОВ В БАЗЕ:")
            print("-" * 40)
            print("Студентов нет. Создаем тестового студента...")
            
            # Создаем тестового студента
            test_student = student_service.create_student(
                name="Тестовый Студент",
                email="test.student@example.com",
                business_role_id=2,  # Frontend Developer
                skills=[
                    {'skill_id': 2, 'proficiency_level': 4},   # JavaScript
                    {'skill_id': 4, 'proficiency_level': 3},   # HTML/CSS
                    {'skill_id': 5, 'proficiency_level': 5},   # React
                    {'skill_id': 8, 'proficiency_level': 3},   # Git
                ]
            )
            
            if 'error' in test_student:
                print(f"Ошибка: {test_student['error']}")
                students = []
            else:
                print(f"Создан студент: {test_student['name']} (ID: {test_student['id']})")
                students = student_service.get_all_students()
        
        # Выводим список студентов
        print("\n1. ПРОВЕРКА СТУДЕНТОВ В БАЗЕ:")
        print("-" * 40)
        for student in students:
            print(f"  ID: {student['id']}, Имя: {student['name']}, Навыков: {student['skills_count']}")
        
        if not students:
            print("Нет студентов для тестирования")
            return
        
        # Тестируем рекомендации для каждого студента
        for student_index, student in enumerate(students, 1):
            print(f"\n{'='*60}")
            print(f"СТУДЕНТ {student_index}/{len(students)}")
            print("=" * 60)
            
            print("\n2. ТЕСТИРОВАНИЕ РЕКОМЕНДАЦИЙ:")
            print("-" * 40)
            print(f"Тестируем рекомендации для студента: {student['name']} (ID: {student['id']})")
            
            student_id = student['id']
            
            # Получаем профиль студента
            profile = student_service.get_student_profile(student_id)
            if profile and profile.get('skills'):
                print(f"Навыки студента:")
                for skill in profile['skills'][:5]:  # Показываем первые 5 навыков
                    stars = "★" * skill['proficiency_level'] + "☆" * (5 - skill['proficiency_level'])
                    print(f"  - {skill['name']}: {stars}")
                if len(profile['skills']) > 5:
                    print(f"  ... и еще {len(profile['skills']) - 5} навыков")
            
            # Получаем рекомендации
            print("\nПоиск рекомендаций...")
            
            try:
                recommendations = recommender.recommend_vacancies_for_student(
                    student_id=student_id,
                    limit=5,
                    min_score=0.3
                )
            except Exception as e:
                print(f"Ошибка при поиске рекомендаций: {e}")
                print("\nПробуем альтернативный подход...")
                
                from app.database.models import Vacancy, Company, Region, BusinessRole, Student
                
                # Получаем студента
                student_obj = db.query(Student).filter(Student.id == student_id).first()
                if not student_obj:
                    print("Студент не найден")
                    continue
                
                # Получаем навыки студента
                student_skills = recommender.get_student_skills(student_id)
                
                # Получаем ВСЕ вакансии
                vacancies_query = db.query(
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
                ).order_by(
                    Vacancy.published_at.desc()
                ).limit(50)  # Ограничиваем 50 вакансиями для теста
                
                recommendations = []
                
                for vacancy, company_name, region_name, business_role_name in vacancies_query.all():
                    # Получаем навыки вакансии
                    vacancy_skills = recommender.get_vacancy_skills(vacancy.id)
                    
                    # Рассчитываем оценки
                    skill_score = recommender.calculate_skill_match_score(student_skills, vacancy_skills)
                    salary_score = recommender.calculate_salary_score(student_id, vacancy.salary_from, vacancy.salary_to)
                    experience_score = recommender.calculate_experience_score(student_id, vacancy.experience)
                    role_score = recommender.calculate_business_role_score(student_id, vacancy.business_role_id)
                    text_similarity = recommender.calculate_text_similarity(student_id, vacancy.description)
                    
                    # Рассчитываем итоговый score
                    final_score = recommender.calculate_final_score(
                        skill_score, salary_score, experience_score, 
                        role_score, text_similarity
                    )
                    
                    # Фильтруем по минимальному score
                    if final_score >= 0.3:
                        recommendation = {
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
                            'scores': {
                                'final_score': final_score,
                                'skill_score': skill_score,
                                'salary_score': salary_score,
                                'experience_score': experience_score,
                                'role_score': role_score,
                                'text_similarity': text_similarity
                            },
                            'matched_skills': recommender._get_matched_skills(student_skills, vacancy_skills),
                            'total_vacancy_skills': len(vacancy_skills)
                        }
                        recommendations.append(recommendation)
                
                # Сортируем по итоговому score
                recommendations.sort(key=lambda x: x['scores']['final_score'], reverse=True)
                recommendations = recommendations[:5]  
            
            if recommendations:
                print(f"\nНайдено {len(recommendations)} рекомендаций:")
                print("-" * 60)
                
                for i, rec in enumerate(recommendations, 1):
                    # Форматируем зарплату
                    salary = ""
                    if rec['salary_from'] or rec['salary_to']:
                        salary = f" ({rec['salary_from'] or '?'}-{rec['salary_to'] or '?'} {rec['currency'] or ''})"
                    
                    print(f"{i}. Score: {rec['scores']['final_score']:.3f}")
                    print(f"   Вакансия: {rec['title'][:50]}...")
                    print(f"   Компания: {rec['company_name']}")
                    print(f"   Регион: {rec['region_name']}{salary}")
                    
                    if rec['matched_skills']:
                        print(f"   Совпавшие навыки: {', '.join(rec['matched_skills'][:3])}")
                        if len(rec['matched_skills']) > 3:
                            print(f"     ... и еще {len(rec['matched_skills']) - 3}")
                    
                    # Детализация оценки
                    print(f"   Детали оценки: Навыки={rec['scores']['skill_score']:.3f}, "
                          f"Опыт={rec['scores']['experience_score']:.3f}, "
                          f"Роль={rec['scores']['role_score']:.3f}")
                    print()
            else:
                print("\nРекомендаций не найдено. Возможные причины:")
                print("1. Нет вакансий в базе данных")
                print("2. Нет совпадений по навыкам")
                print("3. Все рекомендации ниже минимального score")
            
            print("\n3. СТАТИСТИКА:")
            print("-" * 40)
            
            try:
                stats = recommender.get_recommendation_stats(student_id)
                if stats and stats.get('total_recommendations', 0) > 0:
                    print(f"Всего рекомендаций: {stats['total_recommendations']}")
                    print(f"Средний score: {stats['stats']['avg_score']:.3f}")
                    print(f"Лучший score: {stats['stats']['max_score']:.3f}")
                    print(f"Худший score: {stats['stats']['min_score']:.3f}")
                    
                    if stats['stats']['role_distribution']:
                        print(f"Распределение по ролям:")
                        for role, count in stats['stats']['role_distribution'].items():
                            print(f"  - {role}: {count}")
                else:
                    print("Статистика недоступна")
            except Exception as e:
                print(f"Ошибка при получении статистики: {e}")
            
            print(f"\n{'='*60}")
        
        print("\n" + "=" * 80)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        
    except Exception as e:
        print(f"\nОшибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_vacancies_count():
    """Проверка количества вакансий в базе"""
    
    db = SessionLocal()
    
    try:
        from app.database.models import Vacancy
        
        count = db.query(Vacancy).count()
        print(f"Всего вакансий в базе: {count}")
        
        if count == 0:
            print("\n⚠️  ВНИМАНИЕ: В базе нет вакансий!")
            print("   Запустите парсер: python scripts/run_parser.py")
        else:
            # Проверяем, есть ли у вакансий навыки
            vacancies_with_skills = db.query(Vacancy).filter(Vacancy.key_skills != None).count()
            print(f"Вакансий с указанными навыками: {vacancies_with_skills}")
            
            # Покажем несколько примеров
            vacancies = db.query(Vacancy).order_by(Vacancy.id.desc()).limit(3).all()
            print("\nПримеры вакансий:")
            for v in vacancies:
                import json
                skills = json.loads(v.key_skills) if v.key_skills else []
                print(f"  - {v.title}")
                print(f"    Навыки: {', '.join(skills[:3])}" + ("..." if len(skills) > 3 else ""))
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Тестирование системы рекомендаций')
    parser.add_argument('--check', action='store_true', help='Проверить количество вакансий')
    parser.add_argument('--test', action='store_true', help='Запустить тесты рекомендаций')
    
    args = parser.parse_args()
    
    if args.check:
        check_vacancies_count()
    elif args.test:
        test_recommendations_for_all_students()
    else:
        check_vacancies_count()
        print("\n" + "=" * 80)
        test_recommendations_for_all_students()