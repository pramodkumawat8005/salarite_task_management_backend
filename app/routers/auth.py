from fastapi import APIRouter, Depends, HTTPException
from .auth_dtos import RegisterIn, LoginIn, AuthOut, UserOut
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..security import hash_password, verify_password, make_token, current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role not in {"employer", "virtual_hr"}:
        raise HTTPException(422, "Choose Employer or HR as your account type.")
    email = data.email.lower().strip()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = models.User(display_name=data.display_name.strip(),
                       email=email,
                       password_hash=hash_password(data.password), 
                       role=data.role)
    db.add(user); 
    db.commit(); 
    db.refresh(user)
    return AuthOut(access_token=make_token(user), user=UserOut.from_user(user))

@router.post("/login", response_model=AuthOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return AuthOut(access_token=make_token(user), user=UserOut.from_user(user))

@router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(current_user)):
    return UserOut.from_user(user)
