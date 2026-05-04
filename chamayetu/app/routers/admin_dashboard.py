"""
Admin Dashboard Router - Separate admin panel for system administrators.

This provides a separate admin interface for managing the entire platform,
distinct from regular user dashboards. Admin users can:
- View all users and groups
- Monitor system statistics
- Manage M-Pesa configurations
- View platform-wide analytics
"""
from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from app.database import get_db
from app.core.security import get_current_user, verify_password, get_password_hash
from app.models.models import User, Group, Cycle, Contribution, Payout, Notification

router = APIRouter()

# Get templates directory
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "..", "templates")
)


def is_admin_user(db: Session, user_id: int) -> bool:
    """Check if user has admin privileges."""
    user = db.query(User).filter(User.id == user_id).first()
    return user and (user.role == "admin" or user.email == "admin@chamayetu.com")


@router.get("/dashboard")
async def admin_dashboard_page(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Render admin dashboard with platform statistics."""
    user_id = current_user.get("user_id")
    
    # Check admin privileges
    if not is_admin_user(db, user_id):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    # Platform-wide statistics
    total_users = db.query(func.count(User.id)).scalar()
    total_groups = db.query(func.count(Group.id)).scalar()
    active_cycles = db.query(func.count(Cycle.id)).filter(Cycle.status == "active").scalar()
    total_contributions = db.query(func.count(Contribution.id)).scalar()
    total_payouts = db.query(func.count(Payout.id)).scalar()
    
    # Recent activity
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_groups = db.query(Group).order_by(Group.created_at.desc()).limit(5).all()
    recent_cycles = db.query(Cycle).order_by(Cycle.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "title": "Admin Dashboard",
            "current_user": current_user,
            "stats": {
                "total_users": total_users,
                "total_groups": total_groups,
                "active_cycles": active_cycles,
                "total_contributions": total_contributions,
                "total_payouts": total_payouts
            },
            "recent_users": recent_users,
            "recent_groups": recent_groups,
            "recent_cycles": recent_cycles
        }
    )


@router.get("/users")
async def admin_users_page(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    user_id = current_user.get("user_id")
    
    if not is_admin_user(db, user_id):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "title": "Manage Users",
            "current_user": current_user,
            "users": users
        }
    )


@router.get("/groups")
async def admin_groups_page(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all groups (admin only)."""
    user_id = current_user.get("user_id")
    
    if not is_admin_user(db, user_id):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    groups = db.query(Group).order_by(Group.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "admin/groups.html",
        {
            "request": request,
            "title": "Manage Groups",
            "current_user": current_user,
            "groups": groups
        }
    )


@router.get("/setup-admin")
async def setup_admin_page(request: Request):
    """Initial admin setup page (only if no admin exists)."""
    return templates.TemplateResponse(
        "admin/setup.html",
        {"request": request, "title": "Setup Admin Account"}
    )


@router.post("/setup-admin")
async def setup_admin_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create initial admin account."""
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.role == "admin").first()
    
    if existing_admin:
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
    
    # Validation
    errors = []
    
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    if len(password) < 6:
        errors.append("Password must be at least 6 characters")
    
    if errors:
        return templates.TemplateResponse(
            "admin/setup.html",
            {
                "request": request,
                "title": "Setup Admin Account",
                "errors": errors
            }
        )
    
    # Format phone number
    if not phone_number.startswith("254"):
        if phone_number.startswith("07") or phone_number.startswith("01"):
            phone_number = "254" + phone_number[1:]
    
    # Create admin user
    hashed_password = get_password_hash(password)
    admin_user = User(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        hashed_password=hashed_password,
        role="admin"
    )
    
    db.add(admin_user)
    db.commit()
    
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
