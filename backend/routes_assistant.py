from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from database import get_db
from models import User
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


# ============= Request/Response Models =============

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class UsageAnalysis(BaseModel):
    total_verifications: int
    daily_average: float
    weekly_trend: str
    monthly_projection: int
    current_plan: str
    credits_used: int
    credits_limit: int
    credits_remaining: int
    recommended_plan: Optional[str] = None
    cost_savings: Optional[float] = None


class PlanRecommendation(BaseModel):
    recommended_plan_id: str
    plan_name: str
    plan_price: float
    reason: str
    savings: Optional[float] = None
    upgrade_url: str


# ============= Helper Functions =============

async def analyze_user_usage(db, user: User) -> Dict[str, Any]:
    """Analyze user's verification patterns"""
    
    # Get verification history for last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    verifications = await db.verifications.find({
        "user_id": user.id,
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    }).to_list(10000)
    
    total_verifications = len(verifications)
    
    # Calculate daily average
    days_with_data = min(30, (datetime.now(timezone.utc) - thirty_days_ago).days)
    daily_average = total_verifications / days_with_data if days_with_data > 0 else 0
    
    # Calculate weekly trend
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_verifications = [v for v in verifications if datetime.fromisoformat(v['created_at']) >= seven_days_ago]
    
    if total_verifications > 0:
        recent_percentage = (len(recent_verifications) / total_verifications) * 100
        if recent_percentage > 40:
            trend = "increasing"
        elif recent_percentage < 20:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "no_data"
    
    # Project monthly usage
    monthly_projection = int(daily_average * 30)
    
    return {
        "total_verifications": total_verifications,
        "daily_average": round(daily_average, 2),
        "weekly_trend": trend,
        "monthly_projection": monthly_projection,
        "recent_verifications_count": len(recent_verifications)
    }


async def recommend_plan(db, user: User, usage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recommend best plan based on usage"""
    
    monthly_projection = usage_data['monthly_projection']
    current_plan = user.plan
    
    # Get all plans
    plans = await db.plans.find({"is_active": True}, {"_id": 0}).sort("price", 1).to_list(100)
    
    # Find best plan
    current_plan_obj = None
    recommended_plan = None
    
    for plan in plans:
        if plan['type'] == current_plan:
            current_plan_obj = plan
        
        # Find plan that fits projected usage
        if plan['credits_limit'] >= monthly_projection or plan['credits_limit'] == -1:
            if not recommended_plan:
                recommended_plan = plan
            elif plan['price'] < recommended_plan['price']:
                recommended_plan = plan
    
    # Calculate savings
    savings = None
    if recommended_plan and current_plan_obj:
        if recommended_plan['id'] != current_plan_obj['id']:
            # Check if upgrade provides value
            if monthly_projection > current_plan_obj['credits_limit']:
                overage_cost = (monthly_projection - current_plan_obj['credits_limit']) * 0.01  # Assume ₹0.01 per overage
                potential_savings = overage_cost - (recommended_plan['price'] - current_plan_obj['price'])
                if potential_savings > 0:
                    savings = potential_savings
    
    if recommended_plan and (not current_plan_obj or recommended_plan['id'] != current_plan_obj['id']):
        return {
            "plan_id": recommended_plan['id'],
            "plan_name": recommended_plan['name'],
            "plan_price": recommended_plan['price'],
            "credits_limit": recommended_plan['credits_limit'],
            "reason": f"Based on your projected usage of {monthly_projection} verifications/month",
            "savings": savings
        }
    
    return None


def generate_chat_response(user: User, message: str, usage_data: Dict[str, Any], plans: List[Dict]) -> ChatResponse:
    """Generate contextual chat response"""
    
    message_lower = message.lower()
    
    # Plan recommendation queries
    if any(word in message_lower for word in ['plan', 'upgrade', 'recommend', 'need', 'best']):
        monthly_projection = usage_data['monthly_projection']
        
        response = f"Based on your usage pattern of approximately {usage_data['daily_average']} verifications per day "
        response += f"(projected {monthly_projection}/month), "
        
        if monthly_projection < 100:
            suitable_plan = next((p for p in plans if p['type'] == 'free'), None)
            response += f"the **Free plan** (100 verifications/month) should be sufficient for your needs."
        elif monthly_projection < 1000:
            suitable_plan = next((p for p in plans if p['type'] == 'starter'), None)
            response += f"I recommend the **Starter plan** (1,000 verifications/month) at ₹{suitable_plan['price'] if suitable_plan else 'N/A'}/month."
        elif monthly_projection < 5000:
            suitable_plan = next((p for p in plans if p['type'] == 'professional'), None)
            response += f"I recommend the **Professional plan** (5,000 verifications/month) at ₹{suitable_plan['price'] if suitable_plan else 'N/A'}/month."
        else:
            suitable_plan = next((p for p in plans if p['type'] == 'enterprise'), None)
            response += f"I recommend the **Enterprise plan** (Unlimited verifications) at ₹{suitable_plan['price'] if suitable_plan else 'N/A'}/month."
        
        return ChatResponse(
            response=response,
            action="show_plan",
            data=suitable_plan if suitable_plan else None
        )
    
    # Usage queries
    elif any(word in message_lower for word in ['usage', 'used', 'remaining', 'credits', 'stats']):
        credits_remaining = user.credits_limit - user.credits_used
        response = f"You're currently on the **{user.plan}** plan. "
        response += f"You've used **{user.credits_used}** out of **{user.credits_limit}** credits "
        response += f"({credits_remaining} remaining). "
        
        if usage_data['weekly_trend'] == 'increasing':
            response += "Your usage is trending upward. Consider upgrading if you're running low on credits."
        elif user.credits_used / user.credits_limit > 0.8:
            response += "You're using 80%+ of your credits. Time to consider an upgrade?"
        else:
            response += "You're within your limits. Keep verifying!"
        
        return ChatResponse(
            response=response,
            action="show_usage",
            data={
                "credits_used": user.credits_used,
                "credits_limit": user.credits_limit,
                "credits_remaining": credits_remaining,
                "usage_percentage": round((user.credits_used / user.credits_limit) * 100, 1)
            }
        )
    
    # Pricing queries
    elif any(word in message_lower for word in ['price', 'cost', 'pricing', 'how much']):
        response = "Here are our pricing plans:\n\n"
        for plan in plans:
            if plan['price'] == 0:
                response += f"**{plan['name']}**: Free - {plan['credits_limit']} verifications/month\n"
            else:
                credits_text = "Unlimited" if plan['credits_limit'] == -1 else f"{plan['credits_limit']:,}"
                response += f"**{plan['name']}**: ₹{plan['price']}/month - {credits_text} verifications\n"
        
        response += "\nWhich plan interests you?"
        
        return ChatResponse(
            response=response,
            action="show_all_plans",
            data={"plans": plans}
        )
    
    # Help/general queries
    else:
        response = "I'm your MailGuard assistant! I can help you:\n\n"
        response += "• **Check your usage** - Ask about credits, stats, or remaining verifications\n"
        response += "• **Recommend plans** - Get personalized plan recommendations\n"
        response += "• **View pricing** - See all available plans and pricing\n"
        response += "• **Upgrade your plan** - Quick checkout for plan upgrades\n\n"
        response += "What would you like to know?"
        
        return ChatResponse(response=response)


# ============= API Endpoints =============

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """Chat with AI assistant for plan recommendations"""
    db = await get_db()
    
    try:
        # Analyze usage
        usage_data = await analyze_user_usage(db, current_user)
        
        # Get all plans
        plans = await db.plans.find({"is_active": True}, {"_id": 0}).sort("price", 1).to_list(100)
        
        # Generate response
        response = generate_chat_response(current_user, chat_message.message, usage_data, plans)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat assistant: {str(e)}")
        return ChatResponse(
            response="Sorry, I encountered an error. Please try again or contact support."
        )


@router.get("/usage-analysis", response_model=UsageAnalysis)
async def get_usage_analysis(current_user: User = Depends(get_current_user)):
    """Get detailed usage analysis and recommendations"""
    db = await get_db()
    
    try:
        # Analyze usage
        usage_data = await analyze_user_usage(db, current_user)
        
        # Get plan recommendation
        recommendation = await recommend_plan(db, current_user, usage_data)
        
        credits_remaining = current_user.credits_limit - current_user.credits_used
        
        return UsageAnalysis(
            total_verifications=usage_data['total_verifications'],
            daily_average=usage_data['daily_average'],
            weekly_trend=usage_data['weekly_trend'],
            monthly_projection=usage_data['monthly_projection'],
            current_plan=current_user.plan,
            credits_used=current_user.credits_used,
            credits_remaining=credits_remaining,
            recommended_plan=recommendation['plan_name'] if recommendation else None,
            cost_savings=recommendation['savings'] if recommendation else None
        )
        
    except Exception as e:
        logger.error(f"Error in usage analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze usage")


@router.post("/recommend-plan", response_model=PlanRecommendation)
async def get_plan_recommendation(current_user: User = Depends(get_current_user)):
    """Get AI-powered plan recommendation"""
    db = await get_db()
    
    try:
        # Analyze usage
        usage_data = await analyze_user_usage(db, current_user)
        
        # Get recommendation
        recommendation = await recommend_plan(db, current_user, usage_data)
        
        if not recommendation:
            raise HTTPException(
                status_code=200,
                detail="You're on the optimal plan for your usage!"
            )
        
        return PlanRecommendation(
            recommended_plan_id=recommendation['plan_id'],
            plan_name=recommendation['plan_name'],
            plan_price=recommendation['plan_price'],
            reason=recommendation['reason'],
            savings=recommendation.get('savings'),
            upgrade_url=f"/pricing?plan={recommendation['plan_id']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recommending plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendation")
