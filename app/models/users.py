from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from ..database.database import Base


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