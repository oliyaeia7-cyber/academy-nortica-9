from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/blog", tags=["blog"])


@router.post("")
def create_post(payload: schemas.BlogPostCreate, db: Session = Depends(get_db)):
    title = payload.title.strip()
    description = payload.description.strip()
    if not title or not description:
        raise HTTPException(status_code=400, detail="عنوان و متن مقاله نمی‌تواند خالی باشد.")

    post = models.BlogPost(title=title, description=description, slug=None)
    db.add(post)
    db.commit()
    db.refresh(post)

    post.slug = f"maghale-{post.id}"
    db.commit()

    return {"slug": post.slug, "message": "مقاله با موفقیت ذخیره شد."}


@router.put("/{slug}")
def update_post(slug: str, payload: schemas.BlogPostCreate, db: Session = Depends(get_db)):
    title = payload.title.strip()
    description = payload.description.strip()
    if not title or not description:
        raise HTTPException(status_code=400, detail="عنوان و متن مقاله نمی‌تواند خالی باشد.")

    post = db.query(models.BlogPost).filter(models.BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="مقاله مورد نظر پیدا نشد.")

    post.title = title
    post.description = description
    db.commit()

    return {"slug": post.slug, "message": "مقاله با موفقیت ویرایش شد."}


@router.delete("/{slug}")
def delete_post(slug: str, db: Session = Depends(get_db)):
    post = db.query(models.BlogPost).filter(models.BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="مقاله مورد نظر پیدا نشد.")

    db.delete(post)
    db.commit()

    return {"message": "مقاله حذف شد."}
