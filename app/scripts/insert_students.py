# scripts/insert_students.py
"""
Исправленный скрипт для добавления тестовых студентов в базу данных
"""

import sys
import os
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.database.models import Student, Skill, BusinessRole
from sqlalchemy.orm import Session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_skill(db: Session, skill_name: str) -> Skill:
    """Получить существующий навык или создать новый"""
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        skill = Skill(name=skill_name)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        logger.info(f"Создан новый навык: {skill_name}")
    return skill

def add_student_with_skills(
    db: Session,
    name: str,
    email: str,
    business_role_name: str,
    skills: list
):
    """Добавить студента с навыками в базу"""
    
    # Проверяем, существует ли студент с таким email
    existing_student = db.query(Student).filter(Student.email == email).first()
    if existing_student:
        logger.info(f"Студент с email {email} уже существует, пропускаем.")
        return existing_student
    
    # Находим бизнес-роль
    business_role = db.query(BusinessRole).filter(
        BusinessRole.name == business_role_name
    ).first()
    
    if not business_role:
        logger.error(f"Бизнес-роль {business_role_name} не найдена!")
        return None
    
    # Создаем студента
    student = Student(
        name=name,
        email=email,
        business_role_id=business_role.id
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    logger.info(f"Создан студент: {name} (ID: {student.id})")
    
    # Добавляем навыки
    for skill_info in skills:
        skill_name = skill_info['name']
        proficiency_level = skill_info.get('proficiency_level', 3)
        
        skill = get_or_create_skill(db, skill_name)
        
        # Проверяем, нет ли уже такой связи
        existing_link = db.execute(
            text("SELECT 1 FROM msod7.student_skills WHERE student_id = :student_id AND skill_id = :skill_id"),
            {"student_id": student.id, "skill_id": skill.id}
        ).first()
        
        if not existing_link:
            db.execute(
                text("INSERT INTO msod7.student_skills (student_id, skill_id, proficiency_level) VALUES (:student_id, :skill_id, :proficiency_level)"),
                {"student_id": student.id, "skill_id": skill.id, "proficiency_level": proficiency_level}
            )
            db.commit()
            logger.info(f"  - Добавлен навык: {skill_name} (уровень: {proficiency_level})")
    
    return student

def main():
    """Основная функция для добавления студентов"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("ДОБАВЛЕНИЕ ТЕСТОВЫХ СТУДЕНТОВ В БАЗУ ДАННЫХ")
        print("=" * 60)
        
        # Список тестовых студентов (можно изменить по вашему усмотрению)
        test_students = [
            {
                "name": "Свиста Герман",
                "email": "german@college.ru",
                "business_role": "Frontend Developer",
                "skills": [
                    {"name": "JavaScript", "proficiency_level": 5},
                    {"name": "HTML/CSS", "proficiency_level": 5},
                    {"name": "React", "proficiency_level": 5},
                    {"name": "TypeScript", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 4},
                    {"name": "Figma", "proficiency_level": 3}
                ]
            },
            {
                "name": "Петрова Анна",
                "email": "petrova@college.ru",
                "business_role": "Data Analyst",
                "skills": [
                    {"name": "Python", "proficiency_level": 4},
                    {"name": "SQL", "proficiency_level": 5},
                    {"name": "Excel", "proficiency_level": 5},
                    {"name": "Power BI", "proficiency_level": 4},
                    {"name": "Tableau", "proficiency_level": 3},
                    {"name": "Statistics", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 3}
                ]
            },
            {
                "name": "Сидоров Алексей",
                "email": "sidorov@college.ru",
                "business_role": "Backend Developer",
                "skills": [
                    {"name": "Python", "proficiency_level": 5},
                    {"name": "Django", "proficiency_level": 4},
                    {"name": "Flask", "proficiency_level": 4},
                    {"name": "PostgreSQL", "proficiency_level": 4},
                    {"name": "Docker", "proficiency_level": 3},
                    {"name": "Git", "proficiency_level": 4},
                    {"name": "REST API", "proficiency_level": 5}
                ]
            },
            {
                "name": "Кузнецова Екатерина",
                "email": "kuznetsova@college.ru",
                "business_role": "Fullstack Developer",
                "skills": [
                    {"name": "JavaScript", "proficiency_level": 4},
                    {"name": "Python", "proficiency_level": 4},
                    {"name": "React", "proficiency_level": 4},
                    {"name": "Node.js", "proficiency_level": 4},
                    {"name": "MongoDB", "proficiency_level": 3},
                    {"name": "Git", "proficiency_level": 4},
                    {"name": "Docker", "proficiency_level": 3}
                ]
            },
            {
                "name": "Морозов Дмитрий",
                "email": "morozov@college.ru",
                "business_role": "DevOps Engineer",
                "skills": [
                    {"name": "Docker", "proficiency_level": 5},
                    {"name": "Kubernetes", "proficiency_level": 4},
                    {"name": "Linux", "proficiency_level": 5},
                    {"name": "AWS", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 4},
                    {"name": "CI/CD", "proficiency_level": 4},
                    {"name": "Python", "proficiency_level": 3}
                ]
            },
            {
                "name": "Волкова Ольга",
                "email": "volkova@college.ru",
                "business_role": "QA Engineer",
                "skills": [
                    {"name": "Testing", "proficiency_level": 5},
                    {"name": "Automation", "proficiency_level": 4},
                    {"name": "Python", "proficiency_level": 4},
                    {"name": "Selenium", "proficiency_level": 4},
                    {"name": "JIRA", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 3},
                    {"name": "SQL", "proficiency_level": 3}
                ]
            },
            {
                "name": "Никитин Артем",
                "email": "nikitin@college.ru",
                "business_role": "Project Manager",
                "skills": [
                    {"name": "Agile", "proficiency_level": 5},
                    {"name": "Scrum", "proficiency_level": 5},
                    {"name": "JIRA", "proficiency_level": 4},
                    {"name": "Communication", "proficiency_level": 5},
                    {"name": "Leadership", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 2},
                    {"name": "Python", "proficiency_level": 2}
                ]
            },
            {
                "name": "Федорова Мария",
                "email": "fedorova@college.ru",
                "business_role": "UX/UI Designer",
                "skills": [
                    {"name": "Figma", "proficiency_level": 5},
                    {"name": "Adobe XD", "proficiency_level": 4},
                    {"name": "Photoshop", "proficiency_level": 4},
                    {"name": "User Research", "proficiency_level": 4},
                    {"name": "Prototyping", "proficiency_level": 5},
                    {"name": "HTML/CSS", "proficiency_level": 3},
                    {"name": "Git", "proficiency_level": 2}
                ]
            },
            {
                "name": "Григорьев Сергей",
                "email": "grigorev@college.ru",
                "business_role": "Data Scientist",
                "skills": [
                    {"name": "Python", "proficiency_level": 5},
                    {"name": "Machine Learning", "proficiency_level": 4},
                    {"name": "Statistics", "proficiency_level": 5},
                    {"name": "TensorFlow", "proficiency_level": 4},
                    {"name": "SQL", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 3},
                    {"name": "Data Analysis", "proficiency_level": 5}
                ]
            },
            {
                "name": "Белов Андрей",
                "email": "belov@college.ru",
                "business_role": "System Administrator",
                "skills": [
                    {"name": "Linux", "proficiency_level": 5},
                    {"name": "Windows Server", "proficiency_level": 4},
                    {"name": "Networking", "proficiency_level": 4},
                    {"name": "Docker", "proficiency_level": 3},
                    {"name": "Bash", "proficiency_level": 4},
                    {"name": "Git", "proficiency_level": 3},
                    {"name": "Python", "proficiency_level": 2}
                ]
            }
        ]
        
        added_count = 0
        for student_data in test_students:
            print(f"\nДобавление студента: {student_data['name']}")
            print("-" * 40)
            
            student = add_student_with_skills(
                db=db,
                name=student_data['name'],
                email=student_data['email'],
                business_role_name=student_data['business_role'],
                skills=student_data['skills']
            )
            
            if student:
                added_count += 1
                print(f"✓ Успешно добавлен")
        
        print("\n" + "=" * 60)
        print(f"ИТОГО: Добавлено {added_count} студентов")
        
        # Проверяем общее количество студентов
        total_students = db.query(Student).count()
        print(f"Всего студентов в базе: {total_students}")
        
        # Показываем статистику по навыкам
        result = db.execute(
            text("SELECT COUNT(DISTINCT skill_id) FROM msod7.student_skills")
        ).scalar()
        print(f"Уникальных навыков у студентов: {result}")
        
        # Выводим список добавленных студентов
        print("\n" + "=" * 60)
        print("СПИСОК ДОБАВЛЕННЫХ СТУДЕНТОВ:")
        print("=" * 60)
        
        students = db.query(Student).order_by(Student.id.desc()).limit(10).all()
        for student in students:
            # Получаем бизнес-роль
            role = db.query(BusinessRole).filter(BusinessRole.id == student.business_role_id).first()
            role_name = role.name if role else "Не указана"
            
            # Получаем количество навыков
            skills_count = db.execute(
                text("SELECT COUNT(*) FROM msod7.student_skills WHERE student_id = :student_id"),
                {"student_id": student.id}
            ).scalar()
            
            print(f"ID: {student.id}, Имя: {student.name}, Роль: {role_name}, Навыков: {skills_count}")
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении студентов: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("=" * 60)
    print("СКРИПТ ЗАВЕРШЕН УСПЕШНО")
    print("=" * 60)

if __name__ == "__main__":
    main()