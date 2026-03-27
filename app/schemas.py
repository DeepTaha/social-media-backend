from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    age: Optional[int] = None
    bio: Optional[str] = None


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    age: Optional[int] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    title: str
    content: str
    is_public: bool = True


class Post(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    is_public: bool
    likes: int = 0

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str