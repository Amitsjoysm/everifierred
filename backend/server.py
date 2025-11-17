from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import os
from typing import List, Optional
import secrets

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_db
from models import (
    User, UserCreate, UserLogin, UserResponse, Token, OTPVerification,
    PasswordReset, PasswordResetConfirm, OTPStore, EmailVerificationRequest,
    EmailVerificationResult, BulkVerificationJob, APIKey, APIKeyCreate,
    APIKeyResponse, Plan, PlanType, Blog, BlogCreate, FAQ, FAQCreate,
    AnalyticsData, VerificationStatus, UserRole
)
from auth import (
    get_password_hash, verify_password, create_access_token, generate_otp,
    generate_api_key, get_current_active_user, get_current_admin_user,
    get_current_super_admin, verify_api_key
)
from email_service import send_otp_email, send_welcome_email, send_password_reset_email
from email_verifier import verify_single_email
from utils import extract_emails_from_csv, extract_emails_from_excel, extract_emails_from_text
from tasks import verify_bulk_emails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    logger.info("Application shut down")


# ============= Health Check =============

@api_router.get("/")
async def root():
    return {"message": "MailGuard API is running", "status": "healthy"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

