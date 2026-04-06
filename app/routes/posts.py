from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.tasks import send_like_notification

from ..database.database import get_db
from ..models import LikeDB, PostDB, UserDB
from ..schemas.schemas import PostCreate, Post
from ..auth.auth import get_current_user, require_current_user
from typing import Optional

router = APIRouter()


def get_post_with_likes(post: PostDB, db: Session) -> Post:
    """Helper to fetch like count and return a validated Post schema."""
    likes = db.query(func.count(LikeDB.id)).filter(LikeDB.post_id == post.id).scalar()
    return Post(
        id=post.id,
        title=post.title,
        content=post.content,
        is_public=post.is_public,
        owner_id=post.owner_id,
        likes=likes
    )


@router.post("/posts", response_model=Post)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_current_user)
):
    new_post = PostDB(
        title=post.title,
        content=post.content,
        is_public=post.is_public,
        owner_id=current_user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return get_post_with_likes(new_post, db)


@router.get("/posts", response_model=list[Post])
def get_posts(
    db: Session = Depends(get_db),
    current_user: Optional[UserDB] = Depends(get_current_user)
):
    # Logged-in users see all public posts + their own private posts
    # Unauthenticated users see only public posts
    if current_user:
        filter_condition = (
            (PostDB.is_public == True) |
            (PostDB.owner_id == current_user.id)
        )
    else:
        filter_condition = (PostDB.is_public == True)

    rows = (
        db.query(PostDB, func.count(LikeDB.id).label("likes"))
        .outerjoin(LikeDB, PostDB.id == LikeDB.post_id)
        .filter(filter_condition)
        .group_by(PostDB.id)
        .all()
    )

    return [
        Post(
            id=post.id,
            title=post.title,
            content=post.content,
            is_public=post.is_public,
            owner_id=post.owner_id,
            likes=likes
        )
        for post, likes in rows
    ]


@router.get("/posts/{post_id}", response_model=Post)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_current_user)
):
    post = db.query(PostDB).filter(PostDB.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.is_public and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="This post is private")

    return get_post_with_likes(post, db)


@router.get("/users/{user_id}/public-posts", response_model=list[Post])
def get_public_posts_of_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(PostDB, func.count(LikeDB.id).label("likes"))
        .outerjoin(LikeDB, PostDB.id == LikeDB.post_id)
        .filter(PostDB.owner_id == user_id, PostDB.is_public == True)
        .group_by(PostDB.id)
        .all()
    )

    return [
        Post(
            id=post.id,
            title=post.title,
            content=post.content,
            is_public=post.is_public,
            owner_id=post.owner_id,
            likes=likes
        )
        for post, likes in rows
    ]


@router.put("/posts/{post_id}", response_model=Post)
def update_post(
    post_id: int,
    updated_post: PostCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_current_user)
):
    post = db.query(PostDB).filter(PostDB.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    post.title = updated_post.title
    post.content = updated_post.content
    post.is_public = updated_post.is_public

    db.commit()
    db.refresh(post)

    return get_post_with_likes(post, db)


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_current_user)
):
    post = db.query(PostDB).filter(PostDB.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted"}


@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_current_user)
):
    post = db.query(PostDB).filter(PostDB.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.is_public and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot like a private post")

    existing_like = db.query(LikeDB).filter(
        LikeDB.user_id == current_user.id,
        LikeDB.post_id == post_id
    ).first()

    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Post unliked", "liked": False}

    db.add(LikeDB(user_id=current_user.id, post_id=post_id))
    db.commit()

    # fetch post owner email
    post_owner = db.query(UserDB).filter(UserDB.id == post.owner_id).first()

    # trigger background email task
    send_like_notification.delay(
        post_owner_email=post_owner.email,
        post_title=post.title,
        liked_by=current_user.username
    )

    return {"message": "Post liked", "liked": True}