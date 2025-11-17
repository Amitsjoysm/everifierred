import httpx
from config import settings
from models import EmailVerificationResult, ReachabilityStatus
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_confidence_score(
    is_reachable: str,
    is_valid_syntax: bool,
    is_deliverable: bool,
    is_disposable: bool,
    is_disabled: bool,
    can_connect_smtp: bool,
    accepts_mail: bool,
    is_catch_all: bool,
    has_full_inbox: bool
) -> float:
    """Calculate confidence score (0-100) based on verification results"""
    score = 0.0
    
    # Valid syntax (20 points)
    if is_valid_syntax:
        score += 20
    
    # Reachability (30 points)
    if is_reachable == "safe":
        score += 30
    elif is_reachable == "risky":
        score += 15
    
    # Deliverability (25 points)
    if is_deliverable:
        score += 25
    
    # SMTP Connection (10 points)
    if can_connect_smtp:
        score += 10
    
    # Accepts mail (10 points)
    if accepts_mail:
        score += 10
    
    # Negative factors
    if is_disposable:
        score -= 20
    if is_disabled:
        score -= 30
    if has_full_inbox:
        score -= 15
    if is_catch_all:
        score -= 5
    
    # Ensure score is between 0 and 100
    return max(0.0, min(100.0, score))


async def verify_single_email(email: str, max_retries: int = 3) -> Optional[EmailVerificationResult]:
    """Verify a single email using the reacheremail API with retry logic"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.EMAIL_VERIFIER_API}/v0/check_email",
                    json={"to_email": email},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Email verification failed for {email} (attempt {attempt + 1}): {response.text}")
                    last_error = f"API returned status {response.status_code}"
                    
                    # Retry on 5xx errors or timeout
                    if response.status_code >= 500 and attempt < max_retries - 1:
                        continue
                    return None
                
                data = response.json()
            
            # Parse the response
            is_reachable = data.get("is_reachable", "unknown")
            misc = data.get("misc", {})
            mx = data.get("mx", {})
            smtp = data.get("smtp", {})
            syntax = data.get("syntax", {})
            
            # Extract values with defaults
            is_disposable = misc.get("is_disposable", False)
            is_role_account = misc.get("is_role_account", False)
            
            accepts_mail = mx.get("accepts_mail", False)
            mx_records = mx.get("records", [])
            
            can_connect_smtp = smtp.get("can_connect_smtp", False)
            has_full_inbox = smtp.get("has_full_inbox", False)
            is_catch_all = smtp.get("is_catch_all", False)
            is_deliverable = smtp.get("is_deliverable", False)
            is_disabled = smtp.get("is_disabled", False)
            
            is_valid_syntax = syntax.get("is_valid_syntax", False)
            domain = syntax.get("domain", "")
            username = syntax.get("username", "")
            normalized_email = syntax.get("normalized_email", email)
            
            # Calculate confidence score
            confidence_score = calculate_confidence_score(
                is_reachable,
                is_valid_syntax,
                is_deliverable,
                is_disposable,
                is_disabled,
                can_connect_smtp,
                accepts_mail,
                is_catch_all,
                has_full_inbox
            )
            
            # Map is_reachable to enum
            reachability_map = {
                "safe": ReachabilityStatus.SAFE,
                "risky": ReachabilityStatus.RISKY,
                "invalid": ReachabilityStatus.INVALID,
                "unknown": ReachabilityStatus.UNKNOWN
            }
            reachability = reachability_map.get(is_reachable, ReachabilityStatus.UNKNOWN)
            
            result = EmailVerificationResult(
                input=data.get("input", email),
                is_reachable=reachability,
                is_valid_syntax=is_valid_syntax,
                is_disposable=is_disposable,
                is_role_account=is_role_account,
                can_connect_smtp=can_connect_smtp,
                is_deliverable=is_deliverable,
                has_full_inbox=has_full_inbox,
                is_catch_all=is_catch_all,
                is_disabled=is_disabled,
                accepts_mail=accepts_mail,
                mx_records=mx_records,
                confidence_score=confidence_score,
                domain=domain,
                username=username,
                normalized_email=normalized_email
            )
            
            return result
                
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout verifying email {email} (attempt {attempt + 1}): {e}")
            last_error = f"Timeout: {str(e)}"
            if attempt < max_retries - 1:
                continue
        except httpx.RequestError as e:
            logger.warning(f"Network error verifying email {email} (attempt {attempt + 1}): {e}")
            last_error = f"Network error: {str(e)}"
            if attempt < max_retries - 1:
                continue
        except Exception as e:
            logger.error(f"Unexpected error verifying email {email} (attempt {attempt + 1}): {e}")
            last_error = f"Unexpected error: {str(e)}"
            if attempt < max_retries - 1:
                continue
    
    logger.error(f"Failed to verify {email} after {max_retries} attempts. Last error: {last_error}")
    return None
