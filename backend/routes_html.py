"""
Static HTML routes for SEO-friendly pages
These routes serve pre-rendered HTML content without requiring JavaScript
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime
from typing import List
import html

from database import get_db
from models import Blog, FAQ

router = APIRouter(tags=["HTML Pages"])


def generate_html_template(title: str, description: str, content: str, canonical_url: str, structured_data: str = "") -> str:
    """Generate a complete HTML page with SEO optimization"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    
    <!-- Primary Meta Tags -->
    <title>{html.escape(title)}</title>
    <meta name="title" content="{html.escape(title)}">
    <meta name="description" content="{html.escape(description)}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(description)}">
    <meta property="og:site_name" content="MailGuard">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{canonical_url}">
    <meta property="twitter:title" content="{html.escape(title)}">
    <meta property="twitter:description" content="{html.escape(description)}">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{canonical_url}">
    
    <!-- Structured Data -->
    {structured_data}
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px 0;
            margin-bottom: 40px;
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 28px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        nav a {{
            margin-left: 30px;
            color: #555;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }}
        
        nav a:hover {{
            color: #667eea;
        }}
        
        .content {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 40px;
        }}
        
        h1 {{
            font-size: 42px;
            color: #1a202c;
            margin-bottom: 20px;
            line-height: 1.2;
        }}
        
        h2 {{
            font-size: 32px;
            color: #2d3748;
            margin-top: 40px;
            margin-bottom: 20px;
        }}
        
        h3 {{
            font-size: 24px;
            color: #4a5568;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        p {{
            font-size: 18px;
            line-height: 1.8;
            color: #4a5568;
            margin-bottom: 20px;
        }}
        
        .meta {{
            color: #718096;
            font-size: 14px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .meta span {{
            margin-right: 20px;
        }}
        
        ul, ol {{
            margin: 20px 0 20px 40px;
        }}
        
        li {{
            font-size: 18px;
            line-height: 1.8;
            color: #4a5568;
            margin-bottom: 10px;
        }}
        
        .blog-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 4px solid #667eea;
        }}
        
        .blog-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }}
        
        .blog-title {{
            font-size: 28px;
            color: #1a202c;
            margin-bottom: 15px;
        }}
        
        .blog-excerpt {{
            font-size: 16px;
            color: #718096;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        
        .read-more {{
            display: inline-block;
            color: #667eea;
            font-weight: 600;
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        .read-more:hover {{
            color: #764ba2;
        }}
        
        .faq-item {{
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 3px solid #48bb78;
        }}
        
        .faq-question {{
            font-size: 20px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 12px;
        }}
        
        .faq-answer {{
            font-size: 16px;
            color: #4a5568;
            line-height: 1.7;
        }}
        
        .category-badge {{
            display: inline-block;
            background: #e6fffa;
            color: #234e52;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 15px;
        }}
        
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #718096;
            margin-top: 60px;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 32px;
            }}
            
            .header-content {{
                flex-direction: column;
                gap: 15px;
            }}
            
            nav a {{
                margin-left: 15px;
            }}
            
            .content {{
                padding: 25px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="logo">MailGuard</div>
            <nav>
                <a href="/">Home</a>
                <a href="/html/blogs">Blog</a>
                <a href="/html/faqs">FAQs</a>
                <a href="/pricing">Pricing</a>
                <a href="/login">Login</a>
            </nav>
        </div>
    </header>
    
    <main class="container">
        {content}
    </main>
    
    <footer>
        <p>&copy; 2025 MailGuard. All rights reserved. | Professional Email Verification Service</p>
    </footer>
</body>
</html>"""


@router.get("/html/blogs", response_class=HTMLResponse)
async def get_blogs_html():
    """Serve static HTML page with all blog posts"""
    db = await get_db()
    
    # Fetch all published blogs
    blogs = await db.blogs.find(
        {"is_published": True},
        {"_id": 0}
    ).sort("published_at", -1).to_list(100)
    
    if not blogs:
        content = """
        <div class="content">
            <h1>Email Verification Blog</h1>
            <p>No blog posts available at the moment. Check back soon!</p>
        </div>
        """
    else:
        # Generate blog cards
        blog_cards = []
        for blog in blogs:
            published_date = blog.get('published_at', '')
            if isinstance(published_date, str):
                try:
                    published_date = datetime.fromisoformat(published_date).strftime('%B %d, %Y')
                except:
                    published_date = ''
            elif isinstance(published_date, datetime):
                published_date = published_date.strftime('%B %d, %Y')
            
            blog_cards.append(f"""
            <div class="blog-card">
                <h2 class="blog-title">{html.escape(blog.get('title', ''))}</h2>
                <div class="meta">
                    <span>📅 {published_date}</span>
                    <span>✍️ {html.escape(blog.get('author', 'MailGuard Team'))}</span>
                </div>
                <p class="blog-excerpt">{html.escape(blog.get('excerpt', ''))}</p>
                <a href="/html/blog/{blog.get('slug')}" class="read-more">Read Full Article →</a>
            </div>
            """)
        
        content = f"""
        <div class="content">
            <h1>Email Verification Blog</h1>
            <p style="font-size: 20px; color: #718096; margin-bottom: 40px;">
                Expert insights, guides, and best practices for email verification and deliverability.
            </p>
        </div>
        {''.join(blog_cards)}
        """
    
    # Structured data for blog list
    structured_data = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "MailGuard Email Verification Blog",
        "description": "Expert insights and guides on email verification best practices",
        "url": "https://razorpay-integration.preview.emergentagent.com/html/blogs",
        "publisher": {
            "@type": "Organization",
            "name": "MailGuard",
            "logo": {
                "@type": "ImageObject",
                "url": "https://razorpay-integration.preview.emergentagent.com/logo.png"
            }
        }
    }
    </script>
    """
    
    return generate_html_template(
        title="Email Verification Blog - Expert Insights & Best Practices | MailGuard",
        description="Expert insights, guides, and best practices for email verification, deliverability, bounce reduction, and sender reputation management.",
        content=content,
        canonical_url="https://razorpay-integration.preview.emergentagent.com/html/blogs",
        structured_data=structured_data
    )


@router.get("/html/blog/{slug}", response_class=HTMLResponse)
async def get_blog_post_html(slug: str):
    """Serve static HTML page for individual blog post"""
    db = await get_db()
    
    # Fetch blog by slug
    blog = await db.blogs.find_one({"slug": slug, "is_published": True}, {"_id": 0})
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Format published date
    published_date = blog.get('published_at', '')
    if isinstance(published_date, str):
        try:
            published_date = datetime.fromisoformat(published_date).strftime('%B %d, %Y')
        except:
            published_date = ''
    elif isinstance(published_date, datetime):
        published_date = published_date.strftime('%B %d, %Y')
    
    # Convert markdown-style content to HTML paragraphs
    content_text = blog.get('content', '')
    content_paragraphs = []
    
    for paragraph in content_text.split('\n\n'):
        paragraph = paragraph.strip()
        if paragraph:
            # Check if it's a heading
            if paragraph.startswith('# '):
                content_paragraphs.append(f"<h2>{html.escape(paragraph[2:])}</h2>")
            elif paragraph.startswith('## '):
                content_paragraphs.append(f"<h3>{html.escape(paragraph[3:])}</h3>")
            else:
                content_paragraphs.append(f"<p>{html.escape(paragraph)}</p>")
    
    content = f"""
    <div class="content">
        <h1>{html.escape(blog.get('title', ''))}</h1>
        <div class="meta">
            <span>📅 Published: {published_date}</span>
            <span>✍️ By {html.escape(blog.get('author', 'MailGuard Team'))}</span>
        </div>
        {''.join(content_paragraphs)}
        <p style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e2e8f0;">
            <a href="/html/blogs" style="color: #667eea; text-decoration: none; font-weight: 600;">← Back to Blog</a>
        </p>
    </div>
    """
    
    # Structured data for blog post
    structured_data = f"""
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{html.escape(blog.get('title', ''))}",
        "description": "{html.escape(blog.get('excerpt', ''))}",
        "author": {{
            "@type": "Person",
            "name": "{html.escape(blog.get('author', 'MailGuard Team'))}"
        }},
        "datePublished": "{blog.get('published_at', '')}",
        "publisher": {{
            "@type": "Organization",
            "name": "MailGuard",
            "logo": {{
                "@type": "ImageObject",
                "url": "https://razorpay-integration.preview.emergentagent.com/logo.png"
            }}
        }}
    }}
    </script>
    """
    
    return generate_html_template(
        title=f"{blog.get('title', '')} | MailGuard Blog",
        description=blog.get('excerpt', ''),
        content=content,
        canonical_url=f"https://razorpay-integration.preview.emergentagent.com/html/blog/{slug}",
        structured_data=structured_data
    )


@router.get("/html/faqs", response_class=HTMLResponse)
async def get_faqs_html():
    """Serve static HTML page with all FAQs"""
    db = await get_db()
    
    # Fetch all published FAQs
    faqs = await db.faqs.find(
        {"is_published": True},
        {"_id": 0}
    ).sort("order", 1).to_list(1000)
    
    if not faqs:
        content = """
        <div class="content">
            <h1>Frequently Asked Questions</h1>
            <p>No FAQs available at the moment. Check back soon!</p>
        </div>
        """
    else:
        # Group FAQs by category
        categories = {}
        for faq in faqs:
            category = faq.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(faq)
        
        # Generate FAQ items grouped by category
        faq_sections = []
        for category, category_faqs in categories.items():
            faq_items = []
            for faq in category_faqs:
                faq_items.append(f"""
                <div class="faq-item">
                    <div class="faq-question">❓ {html.escape(faq.get('question', ''))}</div>
                    <div class="faq-answer">{html.escape(faq.get('answer', ''))}</div>
                </div>
                """)
            
            faq_sections.append(f"""
            <div style="margin-bottom: 50px;">
                <div class="category-badge">{html.escape(category)}</div>
                {''.join(faq_items)}
            </div>
            """)
        
        content = f"""
        <div class="content">
            <h1>Frequently Asked Questions</h1>
            <p style="font-size: 20px; color: #718096; margin-bottom: 40px;">
                Find answers to common questions about MailGuard email verification service.
            </p>
        </div>
        {''.join(faq_sections)}
        """
    
    # Structured data for FAQs
    faq_schema = []
    for faq in faqs:
        faq_schema.append({
            "@type": "Question",
            "name": faq.get('question', ''),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq.get('answer', '')
            }
        })
    
    import json
    structured_data = f"""
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": {json.dumps(faq_schema)}
    }}
    </script>
    """
    
    return generate_html_template(
        title="FAQs - Email Verification Questions Answered | MailGuard",
        description="Frequently asked questions about MailGuard email verification service. Find answers about pricing, features, API integration, bulk verification, and more.",
        content=content,
        canonical_url="https://razorpay-integration.preview.emergentagent.com/html/faqs",
        structured_data=structured_data
    )
