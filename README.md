# MailGuard - Production-Ready Email Verification Platform

A comprehensive, production-ready email verification SaaS application built with FastAPI, React, and MongoDB.

## 🚀 Features

### Core Functionality
- ✅ Single Email Verification - Real-time verification with instant results
- ✅ Bulk Email Verification - Upload CSV/Excel files for batch processing
- ✅ Async Processing - Redis + Celery workers for high-volume processing (10,000+ users)
- ✅ API Access - RESTful API with API key authentication
- ✅ MCP Server - LLM-accessible verification service
- ✅ Confidence Scoring - 0-100% confidence based on multiple checks

### Authentication & Security
- ✅ JWT Authentication with 2FA OTP via Email
- ✅ Password Reset with secure tokens
- ✅ Rate Limiting (IP-based and API key-based)
- ✅ Security Headers (HSTS, XSS protection, etc.)
- ✅ Best coding practices and SOLID principles

### Subscription & Payments
- ✅ Razorpay Integration (Test keys configured)
- ✅ Multiple Plans: Free, Starter, Professional, Enterprise
- ✅ Credit Management per plan

### Admin Panel
- ✅ Complete user management
- ✅ Plan management with CRUD
- ✅ Blog and FAQ management
- ✅ Analytics dashboard
- ✅ SEO management (JSON-LD, robots.txt, sitemap.xml, llm.txt)

### SEO Optimized
- ✅ 4 SEO-optimized blog posts targeting key phrases
- ✅ 12 comprehensive FAQs
- ✅ JSON-LD structured data
- ✅ Dynamic sitemap and robots.txt

## 🛠️ Technology Stack

**Backend:** FastAPI, MongoDB (Motor), Redis, Celery, Razorpay
**Frontend:** React 19, Tailwind CSS, shadcn/ui
**Infrastructure:** Supervisor, Nginx, Kubernetes-ready

## 🚀 Quick Start

All services are configured and running via Supervisor.

View service status:
```bash
sudo supervisorctl status
```

Services running:
- backend (FastAPI) - Port 8001
- frontend (React) - Port 3000  
- mongodb
- redis
- celery-worker (4 workers)
- celery-beat

## 📊 Default Plans Seeded

1. **Free** - 100 verifications/month - ₹0
2. **Starter** - 1,000 verifications/month - ₹499
3. **Professional** - 5,000 verifications/month - ₹1,999
4. **Enterprise** - 25,000 verifications/month - ₹7,999

## 🔐 API Endpoints

- `/api/auth/*` - Authentication
- `/api/verify` - Email verification (authenticated)
- `/api/external/verify` - External API (API key)
- `/api/mcp/*` - MCP server for LLMs
- `/api/admin/*` - Admin panel
- `/api/content/*` - Blogs and FAQs
- `/api/payments/*` - Razorpay integration
- `/api/plans` - Public pricing plans

Full docs: https://your-domain.com/docs

## 🎯 Production Ready Features

✅ Async workers for 10,000+ concurrent users
✅ Redis + Celery queue system
✅ Security best practices
✅ Rate limiting
✅ SEO optimized pages
✅ MCP server for LLM integration
✅ Complete admin panel
✅ Payment integration ready
✅ All CRUD operations implemented

## 📝 Notes

- Razorpay test keys configured (replace with live keys for production)
- Email verification Docker service: https://fuzzy-space-telegram-jj799979jqr4cqj5-8080.app.github.dev
- SMTP configured with Gmail: gajananzx@gmail.com
