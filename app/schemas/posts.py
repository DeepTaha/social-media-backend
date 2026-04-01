from pydantic import BaseModel


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