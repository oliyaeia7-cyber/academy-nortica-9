from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, Response, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import base64

from database import Base, engine, get_db
import models  # noqa: F401  -> ثبت مدل‌ها روی Base
from assets import LOGO_DATA_URI

import users_router
import plans_router
import chat_planner_router
import study_router
import exams_router
import leaderboard_router
import support_router
import subscription_router
import blog_router

import pages

from redirect_manager import RedirectMiddleware, redirect_manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="نورتیکا | Noortika")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# میدلور Redirect باید بعد از CORS اضافه شود تا در استک ASGI بیرونی‌تر باشد
# و پیش از رسیدن درخواست به روتینگ FastAPI اجرا شود (حتی برای مسیرهای
# حذف‌شده‌ای که دیگر route فعالی ندارند). جزئیات کامل و نحوه‌ی افزودن
# Redirect جدید در redirect_manager.py مستند شده است.
app.add_middleware(RedirectMiddleware, manager=redirect_manager)

app.include_router(users_router.router)
app.include_router(plans_router.router)
app.include_router(chat_planner_router.router)
app.include_router(study_router.router)
app.include_router(exams_router.router)
app.include_router(leaderboard_router.router)
app.include_router(support_router.router)
app.include_router(subscription_router.router)
app.include_router(blog_router.router)

_LOGO_BYTES = base64.b64decode(LOGO_DATA_URI.split(",", 1)[1])


@app.get("/logo.jpg")
def serve_logo():
    return Response(
        content=_LOGO_BYTES,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=604800"},
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    site = pages.SITE_URL or ""
    return (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {site}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
def sitemap_xml():
    site = pages.SITE_URL or ""
    paths = ["/", "/plan", "/exam", "/leaderboard", "/pricing", "/support", "/blog"]
    paths += [f"/blog/{slug}" for slug in pages.BLOG_POSTS.keys()]
    urls = "\n".join(
        f"  <url><loc>{site}{p}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        for p in paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/static/style.css")
def static_style_css():
    return Response(
        content=pages.CSS_TEXT,
        media_type="text/css",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )


@app.get("/static/theme.js")
def static_theme_js():
    return Response(
        content=pages.THEME_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )


@app.get("/", response_class=HTMLResponse)
def home():
    return pages.index_page()


@app.get("/plan", response_class=HTMLResponse)
def plan_page():
    return pages.plan_page()


@app.get("/exam", response_class=HTMLResponse)
def exam_page():
    return pages.exam_page()


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page():
    return pages.leaderboard_page()


@app.get("/pricing", response_class=HTMLResponse)
def pricing_page():
    return pages.pricing_page()


@app.get("/support", response_class=HTMLResponse)
def support_page():
    return pages.support_page()


@app.get("/blog", response_class=HTMLResponse)
def blog_index(db: Session = Depends(get_db)):
    return pages.blog_index_page(db)


@app.get("/blog/{slug}", response_class=HTMLResponse)
def blog_post(slug: str, db: Session = Depends(get_db)):
    html = pages.blog_post_page(slug, db)
    if html is None:
        return HTMLResponse(
            content="<h1 style='font-family:sans-serif;text-align:center;margin-top:80px;'>مقاله مورد نظر پیدا نشد.</h1>"
                    "<p style='text-align:center;'><a href='/blog'>بازگشت به وبلاگ</a></p>",
            status_code=404,
        )
    return HTMLResponse(content=html)
