import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv
from app.database.database import SessionLocal
from app.models import UserDB, PostDB, LikeDB
from sqlalchemy import func, cast, Date
from datetime import date
from app.celery_app import celery
load_dotenv()


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)




@celery.task
def send_like_notification(post_owner_email: str, post_title: str, liked_by: str):
    message = MessageSchema(
        subject="Someone liked your post!",
        recipients=[post_owner_email],
        body=f"""
        Hi,

        {liked_by} liked your post "{post_title}".

        Keep posting great content!

        regards,
        The Team
        """,
        subtype="plain"
    )

    try:
        fm = FastMail(conf)
        # Use sync send instead of async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(fm.send_message(message))
        finally:
            loop.close()
    except Exception as e:
        print(f"Error sending notification: {e}")
        raise

@celery.task
def send_daily_digest():
    db = SessionLocal()

    try:
        # get all users
        users = db.query(UserDB).filter(UserDB.disabled == False).all()

        for user in users:
            # get all post ids of this user
            post_ids = [post.id for post in db.query(PostDB).filter(PostDB.owner_id == user.id).all()]

            if not post_ids:
                continue

            # count likes received today on all their posts
            today = date.today()
            likes_today = db.query(func.count(LikeDB.id)).filter(
                LikeDB.post_id.in_(post_ids),
                cast(LikeDB.created_at, Date) == today
            ).scalar()

            if likes_today == 0:
                continue

            # send email
            message = MessageSchema(
                subject="Your Daily Digest 📊",
                recipients=[user.email],
                body=f"""
                Hi {user.username},

                Here is your daily summary:

                  You received {likes_today} like(s) on your posts today.

                Keep up the great work!

                Regards,
                The Team
                """,
                subtype="plain"
            )

            try:
                fm = FastMail(conf)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(fm.send_message(message))
                finally:
                    loop.close()
            except Exception as e:
                print(f"Error sending digest to {user.email}: {e}")

    finally:
        db.close()