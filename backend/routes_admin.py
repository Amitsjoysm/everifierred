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

@router.post("/users", response_model=UserResponse)
async def create_user(
    email: str,
    full_name: str,
    password: str,
    role: UserRole = UserRole.USER,
    plan: PlanType = PlanType.FREE,
    credits_limit: int = 100,
    current_user: User = Depends(get_current_super_admin)
):
    """Create new user (Super Admin only)"""
    db = await get_db()
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    new_user = User(
        email=email,
        full_name=full_name,
        hashed_password=pwd_context.hash(password),
        role=role,
        plan=plan,
        credits_limit=credits_limit,
        is_verified=True,  # Admin-created users are pre-verified
        is_active=True
    )
    
    user_dict = new_user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['updated_at'] = user_dict['updated_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    return UserResponse(**new_user.model_dump())


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


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: dict,
    current_user: User = Depends(get_current_admin_user)
):
    """Update user details (Admin only)"""
    db = await get_db()
    from passlib.context import CryptContext
    
    # If password is being updated, hash it
    if 'password' in user_update and user_update['password']:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user_update['hashed_password'] = pwd_context.hash(user_update['password'])
        del user_update['password']
    
    # Update timestamp
    user_update['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": user_update}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully"}


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


# ============= Blog Management =============

@router.get("/blogs", response_model=List[Blog])
async def get_all_blogs_admin(current_user: User = Depends(get_current_admin_user)):
    """Get all blogs for admin"""
    db = await get_db()
    
    blogs = await db.blogs.find({}, {"_id": 0}).to_list(100)
    
    for blog in blogs:
        if isinstance(blog.get('created_at'), str):
            blog['created_at'] = datetime.fromisoformat(blog['created_at'])
        if isinstance(blog.get('updated_at'), str):
            blog['updated_at'] = datetime.fromisoformat(blog['updated_at'])
    
    return [Blog(**blog) for blog in blogs]


@router.post("/blogs", response_model=Blog)
async def create_blog_admin(
    blog: BlogCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create new blog post"""
    db = await get_db()
    
    blog_dict = blog.model_dump()
    blog_dict['id'] = str(__import__('uuid').uuid4())
    blog_dict['created_at'] = datetime.now(timezone.utc).isoformat()
    blog_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    blog_dict['slug'] = blog.title.lower().replace(' ', '-').replace('/', '-')
    
    await db.blogs.insert_one(blog_dict)
    
    blog_dict['created_at'] = datetime.fromisoformat(blog_dict['created_at'])
    blog_dict['updated_at'] = datetime.fromisoformat(blog_dict['updated_at'])
    
    return Blog(**blog_dict)


@router.patch("/blogs/{blog_id}")
async def update_blog_admin(
    blog_id: str,
    blog_update: dict,
    current_user: User = Depends(get_current_admin_user)
):
    """Update blog post"""
    db = await get_db()
    
    blog_update['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.blogs.update_one(
        {"id": blog_id},
        {"$set": blog_update}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return {"message": "Blog updated successfully"}


@router.delete("/blogs/{blog_id}")
async def delete_blog_admin(
    blog_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Delete blog post"""
    db = await get_db()
    
    result = await db.blogs.delete_one({"id": blog_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return {"message": "Blog deleted successfully"}


# ============= FAQ Management =============

@router.get("/faqs", response_model=List[FAQ])
async def get_all_faqs_admin(current_user: User = Depends(get_current_admin_user)):
    """Get all FAQs for admin"""
    db = await get_db()
    
    faqs = await db.faqs.find({}, {"_id": 0}).to_list(100)
    
    return [FAQ(**faq) for faq in faqs]


@router.post("/faqs", response_model=FAQ)
async def create_faq_admin(
    faq: FAQCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create new FAQ"""
    db = await get_db()
    
    faq_dict = faq.model_dump()
    faq_dict['id'] = str(__import__('uuid').uuid4())
    
    await db.faqs.insert_one(faq_dict)
    
    return FAQ(**faq_dict)


@router.patch("/faqs/{faq_id}")
async def update_faq_admin(
    faq_id: str,
    faq_update: dict,
    current_user: User = Depends(get_current_admin_user)
):
    """Update FAQ"""
    db = await get_db()
    
    result = await db.faqs.update_one(
        {"id": faq_id},
        {"$set": faq_update}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return {"message": "FAQ updated successfully"}


@router.delete("/faqs/{faq_id}")
async def delete_faq_admin(
    faq_id: str,
    current_user: User = Depends(get_current_super_admin)
):
    """Delete FAQ"""
    db = await get_db()
    
    result = await db.faqs.delete_one({"id": faq_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return {"message": "FAQ deleted successfully"}


# ============= SEO Settings =============

@router.get("/seo-settings")
async def get_seo_settings(current_user: User = Depends(get_current_admin_user)):
    """Get SEO settings"""
    db = await get_db()
    
    settings = await db.seo_settings.find_one({}, {"_id": 0})
    if not settings:
        # Return default settings with HTML page meta tags
        return {
            "robots_txt": """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/""",
            "llm_txt": """# MailGuard - Email Verification Service

## About
MailGuard is a professional email verification service that helps businesses validate email addresses in real-time.

## Features
- Real-time email verification
- Bulk email validation
- API access
- Comprehensive analytics

## Plans
- Free: 100 credits
- Starter: 1,000 credits
- Professional: 10,000 credits
- Enterprise: Unlimited credits

## API
API documentation available at /api/docs""",
            "blog_page_title": "Email Verification Blog - Expert Insights & Best Practices | MailGuard",
            "blog_page_description": "Expert insights, guides, and best practices for email verification, deliverability, bounce reduction, and sender reputation management.",
            "blog_page_keywords": "email verification blog, email validation guide, deliverability tips, sender reputation, bounce rate reduction",
            "faq_page_title": "FAQs - Email Verification Questions Answered | MailGuard",
            "faq_page_description": "Frequently asked questions about MailGuard email verification service. Find answers about pricing, features, API integration, bulk verification, and more.",
            "faq_page_keywords": "email verification FAQ, MailGuard help, email validation questions, API documentation, pricing information"
        }
    
    return settings


@router.post("/seo-settings")
async def update_seo_settings(
    settings: dict,
    current_user: User = Depends(get_current_super_admin)
):
    """Update SEO settings (Super Admin only)"""
    db = await get_db()
    
    await db.seo_settings.update_one(
        {},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "SEO settings updated successfully"}
