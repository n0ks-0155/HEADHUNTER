from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import json

from app.database.session import get_db
from app.services.recommendation import VacancyRecommender
from app.services.student_service import StudentService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("/student/{student_id}")
def get_recommendations_for_student(
    student_id: int,
    limit: int = 10,
    min_score: float = 0.3,
    db: Session = Depends(get_db)
) -> Dict:
    """Получить рекомендации для студента"""
    
    recommender = VacancyRecommender(db)
    
    recommendations = recommender.recommend_vacancies_for_student(
        student_id=student_id,
        limit=limit,
        min_score=min_score
    )
    
    return {
        "student_id": student_id,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    }

@router.get("/student/{student_id}/stats")
def get_recommendation_stats(
    student_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """Получить статистику рекомендаций для студента"""
    
    recommender = VacancyRecommender(db)
    
    stats = recommender.get_recommendation_stats(student_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    return stats

@router.get("/role/{business_role_id}")
def get_recommendations_by_role(
    business_role_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict:
    """Получить рекомендации по бизнес-роли"""
    
    recommender = VacancyRecommender(db)
    
    recommendations = recommender.recommend_vacancies_by_business_role(
        business_role_id=business_role_id,
        limit=limit
    )
    
    return {
        "business_role_id": business_role_id,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    }

@router.post("/student/create")
def create_student_with_recommendations(
    name: str,
    email: str,
    business_role_id: int = None,
    skills_json: str = None,
    db: Session = Depends(get_db)
) -> Dict:
    """Создать студента и сразу получить рекомендации"""
    
    student_service = StudentService(db)
    recommender = VacancyRecommender(db)
    
    # Парсим навыки
    skills = []
    if skills_json:
        try:
            skills_data = json.loads(skills_json)
            skills = [
                {
                    'skill_id': skill.get('skill_id'),
                    'proficiency_level': skill.get('proficiency_level', 1)
                }
                for skill in skills_data
            ]
        except:
            raise HTTPException(status_code=400, detail="Неверный формат навыков")
    
    # Создаем студента
    student = student_service.create_student(
        name=name,
        email=email,
        business_role_id=business_role_id,
        skills=skills
    )
    
    if 'error' in student:
        raise HTTPException(status_code=400, detail=student['error'])
    
    # Получаем рекомендации
    recommendations = recommender.recommend_vacancies_for_student(
        student_id=student['id'],
        limit=10
    )
    
    return {
        "student": student,
        "recommendations": recommendations
    }

@router.get("/students/all")
def get_all_students(
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Получить всех студентов"""
    
    student_service = StudentService(db)
    
    students = student_service.get_all_students()
    
    return students

@router.get("/student/{student_id}/profile")
def get_student_profile(
    student_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """Получить профиль студента"""
    
    student_service = StudentService(db)
    
    profile = student_service.get_student_profile(student_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    return profile
