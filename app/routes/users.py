from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_db
from ...models.models import UserDB
from ..schema.schemas import UserCreate, User, Token
from ..auth.auth import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/signup", response_model=User)
def signup(user: UserCreate, db: Session = Depends(get_db)):

    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    if db.query(UserDB).filter(UserDB.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = UserDB(
        username=user.username,
        email=user.email,
        age=user.age,
        bio=user.bio,
        full_name=user.full_name,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.disabled:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }