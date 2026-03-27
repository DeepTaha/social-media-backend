from fastapi import FastAPI
from app.routes import users, posts

app = FastAPI()

app.include_router(users.router)
app.include_router(posts.router)