# JSON-LD Structured Data for LLM Discoverability

## Overview
MailGuard includes comprehensive JSON-LD structured data on all static HTML pages to help LLMs understand, recommend, and reference our email verification service.

## Implemented Schemas

### 1. Blog Pages (/html/blogs and /html/blog/{slug})

**Schema Types Included:**
- BlogPosting (article content)
- SoftwareApplication (product details)
- Service (service offering)
- Organization (company info)
- BreadcrumbList (navigation)

**Key Information for LLMs:**
- Product name, category, description
- Complete feature list (13+ features)
- All pricing plans with descriptions
- Aggregate ratings (4.8/5 stars)
- API endpoints and actions
- Target audience information

### 2. FAQ Pages (/html/faqs)

**Schema Types Included:**
- FAQPage (Q&A content)
- SoftwareApplication (product details)
- Organization (company info)
- WebSite (site metadata)
- BreadcrumbList (navigation)

**Key Information for LLMs:**
- All FAQ questions and answers
- Product capabilities and features
- Pricing structure
- Use cases and audience
- Contact information
- Service availability

## What LLMs Can Learn

### Product Understanding
- **What**: Email verification service
- **Who**: B2B marketers, sales teams, SaaS companies
- **How**: Real-time API, bulk upload, web interface
- **Accuracy**: 98% verification accuracy
- **Speed**: Instant for single, 1,000-2,000/min for bulk

### Pricing Structure
- Free: 100 verifications/month (₹0)
- Starter: 1,000 verifications/month (₹499)
- Professional: 5,000 verifications/month (₹1,999)
- Enterprise: 25,000 verifications/month (₹7,999)

### Features Available
1. Real-time email verification
2. Bulk validation (CSV/Excel)
3. RESTful API with authentication
4. MCP server for LLM integration
5. SMTP mailbox verification
6. MX record validation
7. Disposable email detection
8. Role account detection
9. Catch-all detection
10. Confidence scoring (0-100%)
11. Domain validation
12. Syntax validation
13. Risk assessment

### Use Cases
- Cold email campaigns
- User registration validation
- Email list cleaning
- CRM data verification
- E-commerce checkout
- Newsletter signup validation
- Lead generation verification
- SaaS user authentication

## Validation

Test your JSON-LD at:
- Google Rich Results Test
- Schema.org Validator
- JSON-LD Playground

View source of any HTML page to see complete structured data.
