from fastapi import FastAPI
from app.routes import users, posts
from app.models import UserDB, PostDB, LikeDB
from app.schemas import User, UserCreate, Post, PostCreate, Token

app = FastAPI()

app.include_router(users.router)
app.include_router(posts.router)