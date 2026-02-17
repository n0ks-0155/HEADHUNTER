from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Table, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

# Указываем схему для всех таблиц
__table_args__ = {'schema': 'msod7'}

# Таблица для связи многие-ко-многим
vacancy_skills = Table(
    'vacancy_skills',
    Base.metadata,
    Column('vacancy_id', Integer, ForeignKey('msod7.vacancies.id', ondelete='CASCADE')),
    Column('skill_id', Integer, ForeignKey('msod7.skills.id', ondelete='CASCADE')),
    schema='msod7'
)

student_skills = Table(
    'student_skills',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('msod7.students.id', ondelete='CASCADE')),
    Column('skill_id', Integer, ForeignKey('msod7.skills.id', ondelete='CASCADE')),
    Column('proficiency_level', Integer),
    schema='msod7'
)

class Company(Base):
    __tablename__ = 'companies'
    __table_args__ = (
        Index('idx_companies_name', 'name'),
        Index('idx_companies_hh_id', 'hh_id'),
        {'schema': 'msod7'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    hh_id = Column(Integer, unique=True, index=True)  # ID компании на HeadHunter
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Отношения
    vacancies = relationship("Vacancy", back_populates="company")

class Region(Base):
    __tablename__ = 'regions'
    __table_args__ = (
        Index('idx_regions_name', 'name'),
        Index('idx_regions_hh_id', 'hh_id'),
        {'schema': 'msod7'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    hh_id = Column(Integer, unique=True, index=True)  # ID региона на HeadHunter
    name = Column(String(100), nullable=False)
    parent_region_id = Column(Integer, ForeignKey('msod7.regions.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    vacancies = relationship("Vacancy", back_populates="region")
    parent_region = relationship("Region", remote_side=[id])

class BusinessRole(Base):
    __tablename__ = 'business_roles'
    __table_args__ = {'schema': 'msod7'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    vacancies = relationship("Vacancy", back_populates="business_role")
    students = relationship("Student", back_populates="business_role")

class Skill(Base):
    __tablename__ = 'skills'
    __table_args__ = {'schema': 'msod7'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    vacancies = relationship("Vacancy", secondary=vacancy_skills, back_populates="skills")
    students = relationship("Student", secondary=student_skills, back_populates="skills")

class Vacancy(Base):
    __tablename__ = 'vacancies'
    __table_args__ = (
        Index('idx_vacancies_title', 'title'),
        Index('idx_vacancies_business_role', 'business_role_id'),
        Index('idx_vacancies_published_at', 'published_at'),
        Index('idx_vacancies_salary_from', 'salary_from'),
        Index('idx_vacancies_company', 'company_id'),
        Index('idx_vacancies_region', 'region_id'),
        Index('idx_vacancies_hh_id', 'hh_id'),
        Index('idx_vacancies_created_at', 'created_at'),
        {'schema': 'msod7'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    hh_id = Column(Integer, unique=True, index=True)
    title = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey('msod7.companies.id'))
    region_id = Column(Integer, ForeignKey('msod7.regions.id'))
    salary_from = Column(Integer)
    salary_to = Column(Integer)
    currency = Column(String(10))
    experience = Column(String(50))
    employment_type = Column(String(50))
    schedule = Column(String(50))
    description = Column(Text)
    key_skills = Column(Text)
    url = Column(String(500))
    published_at = Column(DateTime(timezone=True))
    business_role_id = Column(Integer, ForeignKey('msod7.business_roles.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Отношения
    company = relationship("Company", back_populates="vacancies")
    region = relationship("Region", back_populates="vacancies")
    business_role = relationship("BusinessRole", back_populates="vacancies")
    skills = relationship("Skill", secondary=vacancy_skills, back_populates="vacancies")

class Student(Base):
    __tablename__ = 'students'
    __table_args__ = {'schema': 'msod7'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    business_role_id = Column(Integer, ForeignKey('msod7.business_roles.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    business_role = relationship("BusinessRole", back_populates="students")
    skills = relationship("Skill", secondary=student_skills, back_populates="students")