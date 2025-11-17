from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta, timezone
import secrets
from typing import List

from database import get_db
from models import (
    User, UserCreate, UserLogin, UserResponse, Token, OTPVerification,
    PasswordReset, PasswordResetConfirm, OTPStore
)
from auth import (
    get_password_hash, verify_password, create_access_token, generate_otp,
    get_current_active_user
)
from email_service import send_otp_email, send_welcome_email, send_password_reset_email
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register new user - Step 1: Send OTP"""
    db = await get_db()
    
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    otp_data = OTPStore(
        email=user_data.email,
        otp=otp,
        purpose="registration",
        expires_at=expires_at
    )
    otp_dict = otp_data.model_dump()
    otp_dict['created_at'] = otp_dict['created_at'].isoformat()
    otp_dict['expires_at'] = otp_dict['expires_at'].isoformat()
    
    await db.otp_store.delete_many({"email": user_data.email, "purpose": "registration"})
    await db.otp_store.insert_one(otp_dict)
    
    await send_otp_email(user_data.email, otp, "registration")
    
    temp_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_verified=False
    )
    temp_dict = temp_user.model_dump()
    temp_dict['created_at'] = temp_dict['created_at'].isoformat()
    temp_dict['updated_at'] = temp_dict['updated_at'].isoformat()
    
    await db.temp_users.update_one(
        {"email": user_data.email},
        {"$set": temp_dict},
        upsert=True
    )
    
    return {"message": "OTP sent to your email", "email": user_data.email}


@router.post("/verify-registration", response_model=Token)
async def verify_registration(verification: OTPVerification):
    """Verify OTP and complete registration"""
    db = await get_db()
    
    otp_record = await db.otp_store.find_one({
        "email": verification.email,
        "otp": verification.otp,
        "purpose": "registration",
        "is_used": False
    })
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    expires_at = datetime.fromisoformat(otp_record['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    temp_user = await db.temp_users.find_one({"email": verification.email})
    if not temp_user:
        raise HTTPException(status_code=400, detail="User data not found")
    
    temp_user['is_verified'] = True
    temp_user['is_active'] = True
    await db.users.insert_one(temp_user)
    
    await db.otp_store.update_one(
        {"id": otp_record['id']},
        {"$set": {"is_used": True}}
    )
    
    await db.temp_users.delete_one({"email": verification.email})
    await send_welcome_email(verification.email, temp_user['full_name'])
    
    access_token = create_access_token(data={"sub": temp_user['id']})
    
    if isinstance(temp_user['created_at'], str):
        temp_user['created_at'] = datetime.fromisoformat(temp_user['created_at'])
    
    user_response = UserResponse(**temp_user)
    return Token(access_token=access_token, user=user_response)


@router.post("/login", response_model=dict)
async def login_step1(user_data: UserLogin):
    """Login Step 1: Verify credentials and send OTP"""
    db = await get_db()
    
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user['is_active']:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    otp_data = OTPStore(
        email=user_data.email,
        otp=otp,
        purpose="login",
        expires_at=expires_at
    )
    otp_dict = otp_data.model_dump()
    otp_dict['created_at'] = otp_dict['created_at'].isoformat()
    otp_dict['expires_at'] = otp_dict['expires_at'].isoformat()
    
    await db.otp_store.delete_many({"email": user_data.email, "purpose": "login"})
    await db.otp_store.insert_one(otp_dict)
    
    await send_otp_email(user_data.email, otp, "login")
    
    return {"message": "OTP sent to your email", "email": user_data.email}


@router.post("/verify-login", response_model=Token)
async def verify_login(verification: OTPVerification):
    """Login Step 2: Verify OTP and complete login"""
    db = await get_db()
    
    otp_record = await db.otp_store.find_one({
        "email": verification.email,
        "otp": verification.otp,
        "purpose": "login",
        "is_used": False
    })
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    expires_at = datetime.fromisoformat(otp_record['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    user = await db.users.find_one({"email": verification.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    await db.otp_store.update_one(
        {"id": otp_record['id']},
        {"$set": {"is_used": True}}
    )
    
    access_token = create_access_token(data={"sub": user['id']})
    
    if isinstance(user['created_at'], str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    user_response = UserResponse(**user)
    return Token(access_token=access_token, user=user_response)


@router.post("/forgot-password")
async def forgot_password(data: PasswordReset):
    """Request password reset"""
    db = await get_db()
    
    user = await db.users.find_one({"email": data.email})
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.password_resets.update_one(
        {"email": data.email},
        {
            "$set": {
                "token": reset_token,
                "expires_at": expires_at.isoformat(),
                "is_used": False
            }
        },
        upsert=True
    )
    
    await send_password_reset_email(data.email, reset_token)
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    """Reset password with token"""
    db = await get_db()
    
    reset_record = await db.password_resets.find_one({
        "token": data.token,
        "is_used": False
    })
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    expires_at = datetime.fromisoformat(reset_record['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    hashed_password = get_password_hash(data.new_password)
    await db.users.update_one(
        {"email": reset_record['email']},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    await db.password_resets.update_one(
        {"token": data.token},
        {"$set": {"is_used": True}}
    )
    
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return UserResponse(**current_user.model_dump())
