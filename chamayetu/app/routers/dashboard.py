"""
Dashboard router - displays user dashboard with overview statistics.
"""
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from app.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Group, GroupMember, Cycle, Contribution, Notification

router = APIRouter()

# Get templates directory
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "..", "templates")
)


@router.get("/")
async def dashboard_page(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Render main dashboard page with statistics."""
    user_id = current_user.get("user_id")
    
    # Get user's groups count
    groups_count = db.query(GroupMember).filter(
        GroupMember.user_id == user_id
    ).count()
    
    # Get active cycles count
    active_cycles_count = db.query(Cycle).join(GroupMember, Cycle.group_id == GroupMember.group_id).filter(
        GroupMember.user_id == user_id,
        Cycle.status == "active"
    ).count()
    
    # Get total contributions count
    contributions_count = db.query(Contribution).filter(
        Contribution.user_id == user_id
    ).count()
    
    # Get pending contributions (in active cycles)
    pending_contributions = db.query(Contribution).join(Cycle, Contribution.cycle_id == Cycle.id).filter(
        Contribution.user_id == user_id,
        Cycle.status == "active",
        Contribution.status == "pending"
    ).count()
    
    # Get unread notifications count
    unread_notifications = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()
    
    # Get recent groups
    recent_groups = db.query(Group).join(
        GroupMember, Group.id == GroupMember.group_id
    ).filter(
        GroupMember.user_id == user_id
    ).order_by(Group.created_at.desc()).limit(5).all()
    
    # Get recent activity (latest contributions)
    recent_activity = db.query(Contribution).filter(
        Contribution.user_id == user_id
    ).order_by(Contribution.initiated_at.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        name="dashboard/index.html",
        context={
            "request": request,
            "title": "Dashboard",
            "current_user": current_user,
            "stats": {
                "groups_count": groups_count,
                "active_cycles_count": active_cycles_count,
                "contributions_count": contributions_count,
                "pending_contributions": pending_contributions,
                "unread_notifications": unread_notifications
            },
            "recent_groups": recent_groups,
            "recent_activity": recent_activity
        }
    )
