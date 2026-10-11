from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import ALLOW_REGISTRATION
from ..database import get_db
from ..db_models import User
from ..deps import get_current_user
from ..schemas import Token, UserCreate, UserOut
from ..security import burn_hash_time, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if not ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    username = body.username.strip().lower()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="Username already taken")
    user = User(username=username, hashed_password=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two requests raced for the same username
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already taken")
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form.username.strip().lower()))
    if user is None:
        burn_hash_time(form.password)
        ok = False
    else:
        ok = verify_password(form.password, user.hashed_password)
    if not ok:  # same message for unknown user and wrong password
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
