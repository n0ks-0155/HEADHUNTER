import logging
from typing import List, Dict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class StudentService:
    """Сервис для работы со студентами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_student(
        self, 
        name: str, 
        email: str, 
        business_role_id: int = None,
        skills: List[Dict] = None
    ) -> Dict:
        """Создать нового студента"""
        
        from app.database.models import Student, Skill, student_skills
        
        try:
            # Проверяем, существует ли студент с таким email
            existing = self.db.query(Student).filter(Student.email == email).first()
            if existing:
                logger.warning(f"Студент с email {email} уже существует")
                return {'error': 'Студент с таким email уже существует'}
            
            # Создаем студента
            student = Student(
                name=name,
                email=email,
                business_role_id=business_role_id
            )
            
            self.db.add(student)
            self.db.flush()  # Получаем ID студента
            
            # Добавляем навыки
            if skills:
                for skill_data in skills:
                    skill_id = skill_data.get('skill_id')
                    proficiency = skill_data.get('proficiency_level', 1)
                    
                    # Проверяем существование навыка
                    skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
                    if skill:
                        # Добавляем связь
                        self.db.execute(
                            student_skills.insert().values(
                                student_id=student.id,
                                skill_id=skill_id,
                                proficiency_level=proficiency
                            )
                        )
            
            self.db.commit()
            self.db.refresh(student)
            
            logger.info(f"Создан новый студент: {name} (ID: {student.id})")
            
            return {
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'business_role_id': student.business_role_id,
                'created_at': student.created_at
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании студента: {e}")
            return {'error': str(e)}
    
    def add_student_skill(
        self, 
        student_id: int, 
        skill_id: int, 
        proficiency_level: int = 1
    ) -> bool:
        """Добавить навык студенту"""
        
        from app.database.models import student_skills
        
        try:
            # Проверяем существование связи
            existing = self.db.execute(
                student_skills.select().where(
                    student_skills.c.student_id == student_id,
                    student_skills.c.skill_id == skill_id
                )
            ).first()
            
            if existing:
                # Обновляем уровень владения
                self.db.execute(
                    student_skills.update().where(
                        student_skills.c.student_id == student_id,
                        student_skills.c.skill_id == skill_id
                    ).values(proficiency_level=proficiency_level)
                )
            else:
                # Создаем новую связь
                self.db.execute(
                    student_skills.insert().values(
                        student_id=student_id,
                        skill_id=skill_id,
                        proficiency_level=proficiency_level
                    )
                )
            
            self.db.commit()
            logger.info(f"Добавлен навык {skill_id} студенту {student_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при добавлении навыка: {e}")
            return False
    
    def get_student_profile(self, student_id: int) -> Dict:
        """Получить профиль студента с навыками"""
        
        from app.database.models import Student, Skill, BusinessRole, student_skills
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {}
        
        # Получаем бизнес-роль
        business_role = None
        if student.business_role_id:
            role = self.db.query(BusinessRole).filter(BusinessRole.id == student.business_role_id).first()
            business_role = {
                'id': role.id,
                'name': role.name,
                'description': role.description
            }
        
        # Получаем навыки
        skills_query = self.db.query(
            Skill.id,
            Skill.name,
            Skill.category,
            student_skills.c.proficiency_level
        ).join(
            student_skills, Skill.id == student_skills.c.skill_id
        ).filter(
            student_skills.c.student_id == student_id
        ).all()
        
        skills = [
            {
                'id': skill_id,
                'name': skill_name,
                'category': category,
                'proficiency_level': proficiency_level or 1
            }
            for skill_id, skill_name, category, proficiency_level in skills_query
        ]
        
        return {
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'business_role': business_role,
            'skills': skills,
            'created_at': student.created_at
        }
    
    def update_student_business_role(
        self, 
        student_id: int, 
        business_role_id: int
    ) -> bool:
        """Обновить бизнес-роль студента"""
        
        from app.database.models import Student
        
        try:
            student = self.db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return False
            
            student.business_role_id = business_role_id
            self.db.commit()
            
            logger.info(f"Обновлена бизнес-роль студента {student_id}: {business_role_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении бизнес-роли: {e}")
            return False
    
    def get_all_students(self) -> List[Dict]:
        """Получить список всех студентов"""
        
        from app.database.models import Student, BusinessRole
        
        students_query = self.db.query(
            Student,
            BusinessRole.name.label('business_role_name')
        ).outerjoin(
            BusinessRole, Student.business_role_id == BusinessRole.id
        ).order_by(Student.id).all()
        
        students = []
        for student, business_role_name in students_query:
            # Получаем количество навыков
            from sqlalchemy import func
            from app.database.models import student_skills
            
            skills_count = self.db.query(func.count(student_skills.c.skill_id)).filter(
                student_skills.c.student_id == student.id
            ).scalar() or 0
            
            students.append({
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'business_role': business_role_name,
                'skills_count': skills_count,
                'created_at': student.created_at
            })
        
        return students