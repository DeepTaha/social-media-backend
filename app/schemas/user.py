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