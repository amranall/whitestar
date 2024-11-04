from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from models import User
from sqlalchemy.orm import Session

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else: 
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_access_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

from auth.schemas import UserRead
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token to get the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")  # Extract user_id from payload
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch the user from the database using the user_id
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def role_required(role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user
    return role_checker