from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from app.database.db_config import DatabaseConfig

# Создаем движок
engine = create_engine(
    DatabaseConfig.DATABASE_URL,
    pool_size=DatabaseConfig.POOL_SIZE,
    max_overflow=DatabaseConfig.MAX_OVERFLOW,
    pool_timeout=DatabaseConfig.POOL_TIMEOUT,
    pool_recycle=DatabaseConfig.POOL_RECYCLE
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Указываем схему для всех моделей
Base.metadata.schema = 'msod7'

def get_db():
    """Генератор сессий БД для зависимостей"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_schema_if_not_exists():
    """Создание схемы, если она не существует"""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # Пробуем создать схему, если она не существует
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS msod7"))
            conn.commit()
        print("Схема 'msod7' проверена/создана")
    except Exception as e:
        print(f"Не удалось создать схему 'msod7': {e}")
        # Пробуем использовать public, если нет прав
        Base.metadata.schema = 'public'