import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if it exists
load_dotenv(BASE_DIR / '.env')

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-opportunity-hub-tfest-2026-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Instance directory for sqlite fallback
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_SQLITE_URI = f"sqlite:///{INSTANCE_DIR / 'opportunity_hub.db'}"

    # Database configuration with graceful fallback
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url:
        # Handle postgresql prefix if needed, or mysql
        if _db_url.startswith("postgres://"):
            _db_url = _db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        # Check MySQL specific credentials
        mysql_user = os.environ.get('MYSQL_USER','root')
        mysql_pwd = os.environ.get('MYSQL_PASSWORD','root')
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        mysql_db = os.environ.get('MYSQL_DATABASE', 'opportunity_hub')

        if mysql_user and mysql_pwd:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{mysql_user}:{mysql_pwd}@{mysql_host}:{mysql_port}/{mysql_db}"
        else:
            SQLALCHEMY_DATABASE_URI = DEFAULT_SQLITE_URI

    # Application settings
    APP_NAME = "Student Opportunity Discovery Platform"
    BRAND_NAME = "OpportunityHub"
    ITEMS_PER_PAGE = 9
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'

    # Admin seed defaults
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
    DEMO_STUDENT_EMAIL = os.environ.get('DEMO_STUDENT_EMAIL', 'student@example.com')
    DEMO_STUDENT_PASSWORD = os.environ.get('DEMO_STUDENT_PASSWORD', 'Student@123')


class TestConfig(Config):
    """Testing configuration with in-memory SQLite."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
