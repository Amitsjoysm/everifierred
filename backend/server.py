from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from config import settings
from database import connect_to_mongo, close_mongo_connection
from routes_auth import router as auth_router
from routes_verification import router as verification_router
from routes_apikeys import router as apikeys_router
from routes_external import router as external_router
from routes_admin import router as admin_router
from routes_content import router as content_router
from routes_payments import router as payments_router
from routes_mcp import router as mcp_router

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
api_router.include_router(mcp_router)

# Include API router in main app
app.include_router(api_router)


# SEO Routes - robots.txt, sitemap.xml, llm.txt
@app.get("/robots.txt")
async def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/

Sitemap: {}/sitemap.xml
""".format(settings.APP_URL)
    return content

@app.get("/sitemap.xml")
async def sitemap_xml():
    from database import get_db
    
    db = await get_db()
    blogs = await db.blogs.find({"is_published": True}, {"_id": 0, "slug": 1}).to_list(1000)
    
    urls = [
        settings.APP_URL,
        f"{settings.APP_URL}/pricing",
        f"{settings.APP_URL}/features",
        f"{settings.APP_URL}/blog",
        f"{settings.APP_URL}/faqs",
    ]
    
    for blog in blogs:
        urls.append(f"{settings.APP_URL}/blog/{blog['slug']}")
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        xml_content += f'  <url>\n    <loc>{url}</loc>\n    <changefreq>weekly</changefreq>\n  </url>\n'
    
    xml_content += '</urlset>'
    
    return xml_content

@app.get("/llm.txt")
async def llm_txt():
    content = """# MailGuard - Email Verification Service

## Description
MailGuard is a professional B2B email verification service that helps businesses clean their email lists, reduce bounce rates, and improve email deliverability.

## Features
- Single email verification
- Bulk email verification (CSV/Excel upload)
- API access for developers
- MCP server for LLM integration
- Confidence scoring
- Disposable email detection
- SMTP verification
- MX record validation
- Real-time verification

## API Endpoints
- POST /api/external/verify - Verify email using API key
- POST /api/mcp/verify - MCP server endpoint for LLM integration

## Use Cases
- Email list cleaning for cold email outreach
- Verification for Shopify store owners
- Real estate lead verification
- B2B SaaS email validation
- Recruiter email verification
- Spam trap removal
- Bounce rate reduction

## Contact
Website: {}
API Documentation: {}/docs
""".format(settings.APP_URL, settings.APP_URL)
    return content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
