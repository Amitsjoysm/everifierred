from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from typing import List, Optional

from database import get_db
from models import (
    User, UserResponse, UserRole, Plan, PlanType, Blog, BlogCreate,
    FAQ, FAQCreate, AnalyticsData, Payment
)
from auth import get_current_admin_user, get_current_super_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============= User Management =============

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users (Admin only)"""
    db = await get_db()
    
    query = {}
    if role:
        query['role'] = role
    
    users = await db.users.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if user.get('last_login') and isinstance(user['last_login'], str):
            user['last_login'] = datetime.fromisoformat(user['last_login'])
    
    return [UserResponse(**user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get user by ID"""
    db = await get_db()
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return UserResponse(**user)


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Activate user account"""
    db = await get_db()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User activated successfully"}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Deactivate user account"""
    db = await get_db()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deactivated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Delete user (Super Admin only)"""
    db = await get_db()
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


# ============= Plan Management =============

@router.post("/plans", response_model=Plan)
async def create_plan(
    plan: Plan,
    current_user: User = Depends(get_current_super_admin)
):
    """Create new pricing plan"""
    db = await get_db()
    
    plan_dict = plan.model_dump()
    plan_dict['created_at'] = plan_dict['created_at'].isoformat()
    
    await db.plans.insert_one(plan_dict)
    
    return plan


@router.get("/plans", response_model=List[Plan])
async def get_all_plans(current_user: User = Depends(get_current_admin_user)):
    """Get all pricing plans"""
    db = await get_db()
    
    plans = await db.plans.find({}, {"_id": 0}).to_list(100)
    
    for plan in plans:
        if isinstance(plan.get('created_at'), str):
            plan['created_at'] = datetime.fromisoformat(plan['created_at'])
    
    return [Plan(**plan) for plan in plans]


@router.patch("/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    plan_update: dict,
    current_user: User = Depends(get_current_super_admin)
):
    """Update pricing plan"""
    db = await get_db()
    
    result = await db.plans.update_one(
        {"id": plan_id},
        {"$set": plan_update}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {"message": "Plan updated successfully"}


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Delete pricing plan"""
    db = await get_db()
    
    result = await db.plans.delete_one({"id": plan_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {"message": "Plan deleted successfully"}


# ============= Analytics =============

@router.get("/analytics", response_model=AnalyticsData)
async def get_analytics(current_user: User = Depends(get_current_admin_user)):
    """Get analytics data"""
    db = await get_db()
    
    # Get user statistics
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    
    # Get verification statistics
    total_verifications = await db.email_verifications.count_documents({})
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    verifications_today = await db.email_verifications.count_documents({
        "verified_at": {"$gte": today_start.isoformat()}
    })
    
    # Get revenue statistics
    payments = await db.payments.find({"status": "success"}, {"_id": 0}).to_list(10000)
    revenue_total = sum(p.get('amount', 0) for p in payments)
    
    # Revenue this month
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_payments = [p for p in payments if datetime.fromisoformat(p.get('created_at', '')) >= month_start]
    revenue_month = sum(p.get('amount', 0) for p in month_payments)
    
    # Plan distribution
    plan_distribution = {}
    for plan_type in PlanType:
        count = await db.users.count_documents({"plan": plan_type})
        plan_distribution[plan_type.value] = count
    
    return AnalyticsData(
        total_users=total_users,
        active_users=active_users,
        total_verifications=total_verifications,
        verifications_today=verifications_today,
        revenue_total=revenue_total,
        revenue_month=revenue_month,
        plan_distribution=plan_distribution
    )
