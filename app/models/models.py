from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    age = Column(Integer)
    email = Column(String, unique=True)
    full_name = Column(String)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    bio = Column(String, nullable=True)
  


    posts = relationship("PostDB", back_populates="owner")


class PostDB(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    is_public = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("UserDB", back_populates="posts")


class LikeDB(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_user_post_like"),
    )