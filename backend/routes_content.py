from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List

from database import get_db
from models import Blog, BlogCreate, FAQ, FAQCreate, User
from auth import get_current_admin_user

router = APIRouter(tags=["Content"])


# ============= Blog Management =============

@router.post("/admin/blogs", response_model=Blog)
async def create_blog(
    blog_data: BlogCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create new blog post"""
    db = await get_db()
    
    # Generate slug from title
    slug = blog_data.title.lower().replace(' ', '-').replace('/', '-')
    
    # Check if slug exists
    existing = await db.blogs.find_one({"slug": slug})
    if existing:
        slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"
    
    blog = Blog(
        slug=slug,
        **blog_data.model_dump(),
        published_at=datetime.now(timezone.utc) if blog_data.is_published else None
    )
    
    blog_dict = blog.model_dump()
    blog_dict['created_at'] = blog_dict['created_at'].isoformat()
    blog_dict['updated_at'] = blog_dict['updated_at'].isoformat()
    if blog_dict.get('published_at'):
        blog_dict['published_at'] = blog_dict['published_at'].isoformat()
    
    await db.blogs.insert_one(blog_dict)
    
    return blog


@router.get("/blogs", response_model=List[Blog])
async def get_published_blogs():
    """Get all published blogs"""
    db = await get_db()
    
    blogs = await db.blogs.find(
        {"is_published": True},
        {"_id": 0}
    ).sort("published_at", -1).to_list(100)
    
    for blog in blogs:
        if isinstance(blog.get('created_at'), str):
            blog['created_at'] = datetime.fromisoformat(blog['created_at'])
        if isinstance(blog.get('updated_at'), str):
            blog['updated_at'] = datetime.fromisoformat(blog['updated_at'])
        if blog.get('published_at') and isinstance(blog['published_at'], str):
            blog['published_at'] = datetime.fromisoformat(blog['published_at'])
    
    return [Blog(**blog) for blog in blogs]


@router.get("/blogs/{slug}", response_model=Blog)
async def get_blog_by_slug(slug: str):
    """Get blog by slug"""
    db = await get_db()
    
    blog = await db.blogs.find_one({"slug": slug, "is_published": True}, {"_id": 0})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    if isinstance(blog.get('created_at'), str):
        blog['created_at'] = datetime.fromisoformat(blog['created_at'])
    if isinstance(blog.get('updated_at'), str):
        blog['updated_at'] = datetime.fromisoformat(blog['updated_at'])
    if blog.get('published_at') and isinstance(blog['published_at'], str):
        blog['published_at'] = datetime.fromisoformat(blog['published_at'])
    
    return Blog(**blog)


@router.get("/admin/blogs", response_model=List[Blog])
async def get_all_blogs_admin(current_user: User = Depends(get_current_admin_user)):
    """Get all blogs (Admin)"""
    db = await get_db()
    
    blogs = await db.blogs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for blog in blogs:
        if isinstance(blog.get('created_at'), str):
            blog['created_at'] = datetime.fromisoformat(blog['created_at'])
        if isinstance(blog.get('updated_at'), str):
            blog['updated_at'] = datetime.fromisoformat(blog['updated_at'])
        if blog.get('published_at') and isinstance(blog['published_at'], str):
            blog['published_at'] = datetime.fromisoformat(blog['published_at'])
    
    return [Blog(**blog) for blog in blogs]


@router.patch("/admin/blogs/{blog_id}")
async def update_blog(
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


@router.delete("/admin/blogs/{blog_id}")
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete blog post"""
    db = await get_db()
    
    result = await db.blogs.delete_one({"id": blog_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return {"message": "Blog deleted successfully"}


# ============= FAQ Management =============

@router.post("/admin/faqs", response_model=FAQ)
async def create_faq(
    faq_data: FAQCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Create new FAQ"""
    db = await get_db()
    
    faq = FAQ(**faq_data.model_dump())
    faq_dict = faq.model_dump()
    faq_dict['created_at'] = faq_dict['created_at'].isoformat()
    
    await db.faqs.insert_one(faq_dict)
    
    return faq


@router.get("/faqs", response_model=List[FAQ])
async def get_published_faqs():
    """Get all published FAQs"""
    db = await get_db()
    
    faqs = await db.faqs.find(
        {"is_published": True},
        {"_id": 0}
    ).sort("order", 1).to_list(1000)
    
    for faq in faqs:
        if isinstance(faq.get('created_at'), str):
            faq['created_at'] = datetime.fromisoformat(faq['created_at'])
    
    return [FAQ(**faq) for faq in faqs]


@router.patch("/admin/faqs/{faq_id}")
async def update_faq(
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


@router.delete("/admin/faqs/{faq_id}")
async def delete_faq(
    faq_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Delete FAQ"""
    db = await get_db()
    
    result = await db.faqs.delete_one({"id": faq_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return {"message": "FAQ deleted successfully"}
