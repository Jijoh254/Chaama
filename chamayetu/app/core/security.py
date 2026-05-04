"""
Core security module for authentication and authorization.

Handles:
- Password hashing with bcrypt
- JWT token creation and verification
- OAuth2 password bearer scheme
- Cookie-based session management
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.database import SessionLocal
from app.models.models import User


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme (used for API authentication)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The bcrypt hashed password
        
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token (typically user info)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def authenticate_user(db: SessionLocal, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        User object if authenticated, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user


def get_current_user_from_cookie(request: Request) -> Optional[dict]:
    """
    Extract and verify the current user from JWT cookie.
    
    This is used for web routes that render HTML templates.
    For API routes, use get_current_user dependency instead.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User payload dict if valid token exists, None otherwise
    """
    token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    payload = decode_access_token(token)
    
    if not payload:
        return None
    
    # Check token hasn't expired
    exp = payload.get("exp")
    if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
        return None
    
    return payload


def get_current_user(request: Request) -> Optional[dict]:
    """
    Dependency to get current user from JWT cookie.
    
    Use this in route handlers to require authentication.
    Raises HTTPException if not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User payload dict
        
    Raises:
        HTTPException: 302 redirect to login if not authenticated
    """
    user = get_current_user_from_cookie(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/auth/login"}
        )
    
    return user


def get_optional_current_user(request: Request) -> Optional[dict]:
    """
    Get current user if logged in, None otherwise.
    
    Unlike get_current_user, this doesn't raise an exception
    if the user is not authenticated. Useful for pages that
    show different content based on login status.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User payload dict or None
    """
    return get_current_user_from_cookie(request)
