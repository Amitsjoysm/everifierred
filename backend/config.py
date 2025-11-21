from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'email_verifier_db')
    
    # Redis
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Email (Gmail SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = os.environ.get('SMTP_USER', 'gajananzx@gmail.com')
    SMTP_PASSWORD: str = os.environ.get('SMTP_PASSWORD', 'wbhnyrwyvhidajfe')
    
    # Email Verifier API
    EMAIL_VERIFIER_API: str = os.environ.get('EMAIL_VERIFIER_API', 'http://localhost:8080')
    EMAIL_VERIFIER_API_FALLBACK: str = os.environ.get('EMAIL_VERIFIER_API_FALLBACK', 'http://158.69.113.127:8080')
    
    # Razorpay
    RAZORPAY_KEY_ID: str = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET: str = os.environ.get('RAZORPAY_KEY_SECRET', '')
    
    # CORS
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')
    
    # App
    APP_NAME: str = "MailGuard - Email Verifier"
    APP_URL: str = os.environ.get('APP_URL', 'http://localhost:3000')
    
    # File Storage
    UPLOAD_DIR: Path = Path("/app/backend/uploads")
    RESULTS_DIR: Path = Path("/app/backend/results")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create directories
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
