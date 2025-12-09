from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from pathlib import Path
import logging

from config import settings
from database import connect_to_mongo, close_mongo_connection
from middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    APIKeyRateLimitMiddleware
)
from routes_auth import router as auth_router
from routes_verification import router as verification_router
from routes_apikeys import router as apikeys_router
from routes_external import router as external_router
from routes_admin import router as admin_router
from routes_content import router as content_router
from routes_payments import router as payments_router
from routes_payment_admin import router as payment_admin_router
from routes_subscriptions import router as subscriptions_router
from routes_mcp import router as mcp_router
from routes_assistant import router as assistant_router
from routes_html import router as html_router

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

# Security Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(APIKeyRateLimitMiddleware, requests_per_minute=100)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(',') if settings.CORS_ORIGINS != '*' else ['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    logger.info("Application shut down")


# Health check routes
@api_router.get("/")
async def root():
    return {"message": "MailGuard API is running", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include all routers
api_router.include_router(auth_router)
api_router.include_router(verification_router)
api_router.include_router(apikeys_router)
api_router.include_router(external_router)
api_router.include_router(admin_router)
api_router.include_router(content_router)
api_router.include_router(payments_router)
api_router.include_router(payment_admin_router)
api_router.include_router(subscriptions_router)
api_router.include_router(mcp_router)
api_router.include_router(assistant_router)

# Include API router in main app
app.include_router(api_router)

# Include HTML router (for static HTML pages - SEO friendly)
app.include_router(html_router)


# SEO Routes - robots.txt, sitemap.xml, llm.txt
@app.get("/robots.txt")
async def robots_txt():
    from database import get_db
    
    db = await get_db()
    seo_settings = await db.seo_settings.find_one({}, {"_id": 0})
    
    if seo_settings and 'robots_txt' in seo_settings:
        content = seo_settings['robots_txt']
    else:
        content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/"""
    
    # Add sitemap reference if not present
    if 'Sitemap:' not in content:
        content += f"\n\nSitemap: {settings.APP_URL}/sitemap.xml"
    
    return content

@app.get("/sitemap.xml")
async def sitemap_xml():
    from database import get_db
    from datetime import datetime
    
    db = await get_db()
    blogs = await db.blogs.find({"is_published": True}, {"_id": 0, "slug": 1, "updated_at": 1}).to_list(1000)
    
    # Static pages with priority
    static_urls = [
        {"loc": settings.APP_URL, "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{settings.APP_URL}/pricing", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{settings.APP_URL}/features", "priority": "0.8", "changefreq": "weekly"},
        {"loc": f"{settings.APP_URL}/blog", "priority": "0.8", "changefreq": "daily"},
        {"loc": f"{settings.APP_URL}/faqs", "priority": "0.7", "changefreq": "weekly"},
    ]
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    xml_content += 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    
    # Add static pages
    for url_data in static_urls:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{url_data["loc"]}</loc>\n'
        xml_content += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
        xml_content += f'    <changefreq>{url_data["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{url_data["priority"]}</priority>\n'
        xml_content += '  </url>\n'
    
    # Add blog posts
    for blog in blogs:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{settings.APP_URL}/blog/{blog["slug"]}</loc>\n'
        lastmod = blog.get("updated_at", datetime.utcnow().isoformat())[:10]
        xml_content += f'    <lastmod>{lastmod}</lastmod>\n'
        xml_content += '    <changefreq>monthly</changefreq>\n'
        xml_content += '    <priority>0.6</priority>\n'
        xml_content += '  </url>\n'
    
    xml_content += '</urlset>'
    
    return xml_content

@app.get("/llm.txt")
async def llm_txt():
    from database import get_db
    
    db = await get_db()
    
    # Check if custom SEO settings exist
    seo_settings = await db.seo_settings.find_one({}, {"_id": 0})
    
    if seo_settings and 'llm_txt' in seo_settings and seo_settings['llm_txt']:
        return seo_settings['llm_txt']
    
    # Otherwise, generate default content
    blogs = await db.blogs.find({"is_published": True}, {"_id": 0, "title": 1, "slug": 1, "excerpt": 1}).to_list(10)
    faqs = await db.faqs.find({"is_published": True}, {"_id": 0, "question": 1, "answer": 1, "category": 1}).to_list(20)
    
    content = """# MailGuard - Professional Email Verification Service

## Description
MailGuard is a professional B2B email verification service that helps businesses clean their email lists, reduce bounce rates by up to 98%, and improve email deliverability. Our advanced verification technology uses SMTP, MX record validation, and disposable email detection to ensure the highest accuracy.

## Core Features
- **Single Email Verification**: Verify individual email addresses in real-time
- **Bulk Email Verification**: Upload CSV/Excel files with up to 10,000 emails
- **API Access**: RESTful API for seamless integration with your applications
- **MCP Server**: LLM integration for AI-powered email verification
- **Confidence Scoring**: 0-100% confidence score for each verification
- **Disposable Email Detection**: Identify temporary and disposable email addresses
- **SMTP Verification**: Real-time mailbox verification
- **MX Record Validation**: Verify domain mail server configuration
- **Role Account Detection**: Identify generic email addresses (info@, admin@)
- **Catch-all Detection**: Detect domains that accept all emails

## Verification Methods
1. **Syntax Validation**: Check email format and structure
2. **Domain Verification**: Validate domain exists and has MX records
3. **SMTP Check**: Connect to mail server and verify mailbox
4. **Disposable Detection**: Check against database of temporary email providers
5. **Risk Assessment**: Analyze patterns and assign confidence score

## API Endpoints
- `POST /api/external/verify` - Verify single email using API key
- `POST /api/external/verify-bulk` - Verify multiple emails (up to 100)
- `POST /api/mcp/verify` - MCP server endpoint for LLM integration
- `GET /api/plans` - Get pricing plans information
- `GET /api/content/blogs` - Access blog content
- `GET /api/content/faqs` - Access FAQ content

## Pricing Plans
- **Free Plan**: 100 verifications/month - Perfect for testing
- **Starter Plan**: 1,000 verifications/month - For small businesses
- **Professional Plan**: 5,000 verifications/month - For growing teams
- **Enterprise Plan**: 25,000 verifications/month - For large organizations

## Use Cases
- **Cold Email Outreach**: Clean email lists before campaigns to avoid spam filters
- **E-commerce**: Verify customer emails during checkout to reduce fraud
- **B2B Lead Generation**: Validate prospect emails before sales outreach
- **Email Marketing**: Reduce bounce rates and improve sender reputation
- **SaaS User Verification**: Ensure valid emails during user registration
- **Recruitment**: Verify candidate email addresses
- **Real Estate**: Validate lead emails from property listings
- **Newsletter Signups**: Prevent fake email subscriptions

## Blog Content
"""
    
    for blog in blogs:
        content += f"\n### {blog['title']}\n"
        content += f"{blog['excerpt']}\n"
        content += f"Read more: {settings.APP_URL}/blog/{blog['slug']}\n"
    
    content += "\n## Frequently Asked Questions\n"
    
    for faq in faqs[:10]:
        content += f"\n**Q: {faq['question']}**\n"
        content += f"A: {faq['answer']}\n"
    
    content += f"""
## Technical Integration
- RESTful API with JSON responses
- API key authentication
- Rate limiting: 100 requests/minute per API key
- Webhook support for async processing
- OpenAPI/Swagger documentation available at {settings.APP_URL}/docs

## Security & Compliance
- GDPR compliant
- SOC 2 Type II certified (in progress)
- Data encrypted in transit and at rest
- No email content is stored
- API keys encrypted with industry-standard encryption

## Performance
- Average response time: < 200ms
- 99.9% uptime SLA
- Global CDN for fast access worldwide
- Redundant infrastructure
- Real-time verification

## Contact & Support
- Website: {settings.APP_URL}
- API Documentation: {settings.APP_URL}/docs
- Blog: {settings.APP_URL}/blog
- FAQs: {settings.APP_URL}/faqs
- Email: support@mailguard.com

## For LLMs & AI Agents
This service can be integrated into AI workflows for:
1. Automated email list cleaning
2. Lead validation in CRM systems
3. User verification in authentication flows
4. Fraud detection in e-commerce
5. Quality assurance for marketing campaigns

Use the MCP endpoints for seamless LLM integration.
"""
    
    return content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
