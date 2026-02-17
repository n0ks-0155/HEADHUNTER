import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    DB_HOST = os.getenv('DB_HOST', 'your_host')
    DB_PORT = os.getenv('DB_PORT', 'your_port')
    DB_NAME = os.getenv('DB_NAME', 'your_name')
    DB_USER = os.getenv('DB_USER', 'your_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Настройки пула соединений
    POOL_SIZE = 20
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600
