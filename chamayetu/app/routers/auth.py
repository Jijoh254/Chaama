"""
Authentication router - handles user registration, login, and logout.

All routes render HTML templates (Jinja2) for server-side rendering.
Authentication uses JWT stored in HTTP-only cookies.
"""
from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.core.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_optional_current_user
)
from app.models.models import User

router = APIRouter()

# Get templates directory
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "..", "templates")
)


@router.get("/login")
async def login_page(
    request: Request,
    current_user: dict = Depends(get_optional_current_user)
):
    """Render login page."""
    # If already logged in, redirect to dashboard
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Login"}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login form submission."""
    # Authenticate user
    user = authenticate_user(db, email, password)
    
    if not user:
        # Invalid credentials - re-render login with error
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "title": "Login",
                "error": "Invalid email or password"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "full_name": user.full_name}
    )
    
    # Create redirect response with cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Prevent JavaScript access
        secure=False,   # Set True in production with HTTPS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return response


@router.get("/register")
async def register_page(
    request: Request,
    current_user: dict = Depends(get_optional_current_user)
):
    """Render registration page."""
    # If already logged in, redirect to dashboard
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "title": "Register"}
    )


@router.post("/register")
async def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process registration form submission."""
    # Validation
    errors = []
    
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    if len(password) < 6:
        errors.append("Password must be at least 6 characters")
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        errors.append("Email already registered")
    
    # Check if phone number already exists
    existing_phone = db.query(User).filter(User.phone_number == phone_number).first()
    if existing_phone:
        errors.append("Phone number already registered")
    
    # Format phone number (ensure it starts with 254)
    if not phone_number.startswith("254"):
        if phone_number.startswith("07") or phone_number.startswith("01"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+254"):
            phone_number = phone_number[1:]
    
    if errors:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "title": "Register",
                "errors": errors,
                "form_data": {
                    "full_name": full_name,
                    "email": email,
                    "phone_number": phone_number
                }
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        hashed_password=hashed_password,
        role="member"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id, "full_name": new_user.full_name}
    )
    
    # Create redirect response with cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return response


@router.get("/logout")
async def logout(request: Request):
    """Logout user by clearing the access token cookie."""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response


# Import settings here to avoid circular imports
from app.core.config import settings
