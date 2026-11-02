"""JWT authentication helpers. Set a long random JWT_SECRET in production."""
import os
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from . import models

SECRET = os.getenv("JWT_SECRET", "dev-only-change-this-secret-before-deployment")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def make_token(user: models.User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user.id), "role": user.role, "iat": now,
                       "exp": now + timedelta(hours=12)}, SECRET, algorithm=ALGORITHM)

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, "Please sign in to continue.", headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
        uid = int(payload.get("sub", "0"))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(401, "Your session has expired. Please sign in again.", headers={"WWW-Authenticate":"Bearer"})
    user = db.query(models.User).filter(models.User.id == uid).first()
    if not user: raise HTTPException(401, "Account no longer exists.")
    return user

def require_role(*roles):
    def checker(user: models.User = Depends(current_user)):
        if user.role not in roles: raise HTTPException(403, "You do not have permission to perform this action.")
        return user
    return checker
