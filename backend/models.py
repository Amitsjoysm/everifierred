from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReachabilityStatus(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    plan: str = "free"  # Changed from PlanType enum to str
    credits_used: int = 0
    credits_limit: int = 100
    api_calls_count: int = 0


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.USER
    plan: str = "free"
    credits_limit: int = 100


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    two_fa_enabled: bool = False
    two_fa_secret: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    two_fa_enabled: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class OTPStore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    otp: str
    purpose: str  # "registration", "login", "password_reset"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_used: bool = False


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationResult(BaseModel):
    input: str
    is_reachable: ReachabilityStatus
    is_valid_syntax: bool
    is_disposable: bool
    is_role_account: bool
    can_connect_smtp: bool
    is_deliverable: bool
    has_full_inbox: bool
    is_catch_all: bool
    is_disabled: bool
    accepts_mail: bool
    mx_records: List[str]
    confidence_score: float
    domain: str
    username: str
    normalized_email: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BulkEmailVerificationRequest(BaseModel):
    emails: List[EmailStr]


class BulkVerificationJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: VerificationStatus = VerificationStatus.PENDING
    total_emails: int
    processed_emails: int = 0
    successful: int = 0
    failed: int = 0
    file_url: Optional[str] = None
    result_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class APIKey(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key: str
    name: str
    is_active: bool = True
    calls_count: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class APIKeyCreate(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    is_active: bool
    calls_count: int
    created_at: datetime


class Plan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # Changed from PlanType enum to str for flexibility
    credits_limit: int
    
    # Monthly pricing
    price: float  # Current monthly price (after discount)
    original_price: Optional[float] = None  # Hyped/original monthly price for marketing
    discount_percentage: float = 0  # Discount percentage for monthly
    
    # Yearly pricing
    yearly_price: Optional[float] = None  # Current yearly price (after discount)
    yearly_original_price: Optional[float] = None  # Hyped/original yearly price
    yearly_discount_percentage: float = 0  # Discount percentage for yearly
    
    # International pricing
    price_usd: Optional[float] = None  # USD price for international customers
    currency: str = "INR"  # Default currency
    
    # Razorpay subscription IDs
    razorpay_plan_id_monthly: Optional[str] = None  # Razorpay subscription plan ID for monthly
    razorpay_plan_id_yearly: Optional[str] = None  # Razorpay subscription plan ID for yearly
    
    # Legacy fields for backward compatibility
    billing_cycle: str = "monthly"  # monthly, yearly (default view)
    razorpay_plan_id: Optional[str] = None  # Deprecated: for one-time payments
    razorpay_plan_id_inr: Optional[str] = None  # Deprecated
    razorpay_plan_id_usd: Optional[str] = None  # Deprecated
    
    is_recurring: bool = True  # True for subscription plans
    features: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan_id: str
    amount: float
    currency: str = "INR"
    billing_cycle: str = "monthly"  # monthly or yearly
    
    # Razorpay IDs
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    razorpay_subscription_id: Optional[str] = None  # For recurring subscriptions
    
    status: str = "pending"  # pending, success, failed, cancelled, expired
    is_recurring: bool = False  # True for subscription payments
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None  # For subscriptions



class PaymentVerifyRequest(BaseModel):
    """Request model for payment verification"""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: str


class Blog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    title: str
    content: str
    excerpt: str
    author: str
    meta_title: str
    meta_description: str
    keywords: List[str]
    is_published: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FAQ(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    answer: str
    category: str
    order: int = 0
    is_published: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BlogCreate(BaseModel):
    title: str
    content: str
    excerpt: str
    author: str
    meta_title: str
    meta_description: str
    keywords: List[str]
    is_published: bool = False


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str
    order: int = 0


class AnalyticsData(BaseModel):
    total_users: int
    active_users: int
    total_verifications: int
    verifications_today: int
    revenue_total: float
    revenue_month: float
    plan_distribution: Dict[str, int]




class TransactionType(str, Enum):
    VERIFICATION = "verification"
    BULK_JOB = "bulk_job"
    PURCHASE = "purchase"
    REFUND = "refund"
    RESET = "reset"


class CreditTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_type: TransactionType
    credits_change: int  # Positive for credit, negative for debit
    credits_before: int
    credits_after: int
    description: str
    reference_id: Optional[str] = None  # Job ID, verification ID, payment ID etc
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
