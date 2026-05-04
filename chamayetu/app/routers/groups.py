"""
Groups router - handles group CRUD operations, joining, and cycle management.
"""
from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import secrets

from app.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Group, GroupMember, Cycle, Notification

router = APIRouter()

# Get templates directory
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "..", "templates")
)


@router.get("/")
async def groups_list(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all user's groups."""
    user_id = current_user.get("user_id")
    
    # Get all groups user is a member of
    user_groups = db.query(Group).join(
        GroupMember, Group.id == GroupMember.group_id
    ).filter(
        GroupMember.user_id == user_id
    ).order_by(Group.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "groups/list.html",
        {
            "request": request,
            "title": "My Groups",
            "current_user": current_user,
            "groups": user_groups
        }
    )


@router.post("/")
async def create_group(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    contribution_amount: float = Form(...),
    frequency: str = Form(...),
    max_members: int = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new group."""
    # Generate unique 8-character invite code
    invite_code = secrets.token_urlsafe(6)[:8].upper()
    
    # Create group
    new_group = Group(
        name=name,
        description=description,
        contribution_amount=contribution_amount,
        frequency=frequency,
        max_members=max_members,
        invite_code=invite_code,
        created_by=current_user.get("user_id")
    )
    
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    # Add creator as first member with queue_position 1
    creator_membership = GroupMember(
        group_id=new_group.id,
        user_id=current_user.get("user_id"),
        queue_position=1
    )
    db.add(creator_membership)
    db.commit()
    
    return RedirectResponse(url=f"/groups/{new_group.id}", status_code=status.HTTP_302_FOUND)


@router.get("/{group_id}")
async def group_detail(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show group details including members, cycles, and contributions."""
    user_id = current_user.get("user_id")
    
    # Get group
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        return RedirectResponse(url="/groups", status_code=status.HTTP_302_FOUND)
    
    # Check if user is member
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    
    if not membership:
        return RedirectResponse(url="/groups", status_code=status.HTTP_302_FOUND)
    
    # Get members ordered by queue position
    members = db.query(GroupMember).join(User).filter(
        GroupMember.group_id == group_id
    ).order_by(GroupMember.queue_position).all()
    
    # Get cycles
    cycles = db.query(Cycle).filter(
        Cycle.group_id == group_id
    ).order_by(Cycle.cycle_number.desc()).all()
    
    # Get active cycle
    active_cycle = db.query(Cycle).filter(
        Cycle.group_id == group_id,
        Cycle.status == "active"
    ).first()
    
    return templates.TemplateResponse(
        "groups/detail.html",
        {
            "request": request,
            "title": group.name,
            "current_user": current_user,
            "group": group,
            "members": members,
            "cycles": cycles,
            "active_cycle": active_cycle,
            "membership": membership
        }
    )


@router.post("/join")
async def join_group(
    request: Request,
    invite_code: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a group using invite code."""
    user_id = current_user.get("user_id")
    
    # Find group by invite code
    group = db.query(Group).filter(
        Group.invite_code == invite_code.upper()
    ).first()
    
    if not group:
        # Invalid invite code
        return RedirectResponse(url="/groups?error=invalid_code", status_code=status.HTTP_302_FOUND)
    
    # Check if already member
    existing_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == user_id
    ).first()
    
    if existing_membership:
        return RedirectResponse(url=f"/groups/{group.id}", status_code=status.HTTP_302_FOUND)
    
    # Check if group is full
    member_count = db.query(GroupMember).filter(
        GroupMember.group_id == group.id
    ).count()
    
    if member_count >= group.max_members:
        return RedirectResponse(url="/groups?error=group_full", status_code=status.HTTP_302_FOUND)
    
    # Get next queue position
    next_position = member_count + 1
    
    # Add member
    new_membership = GroupMember(
        group_id=group.id,
        user_id=user_id,
        queue_position=next_position
    )
    db.add(new_membership)
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group.id}", status_code=status.HTTP_302_FOUND)


@router.post("/{group_id}/start-cycle")
async def start_cycle(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new contribution cycle (admin only)."""
    user_id = current_user.get("user_id")
    
    # Get group
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group or group.created_by != user_id:
        return RedirectResponse(url="/groups", status_code=status.HTTP_403_FOUND)
    
    # Get next beneficiary (member who hasn't received yet, lowest queue position)
    next_beneficiary = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.has_received == False
    ).order_by(GroupMember.queue_position).first()
    
    if not next_beneficiary:
        # All members have received - cycle complete
        return RedirectResponse(url=f"/groups/{group_id}?error=cycle_complete", status_code=status.HTTP_302_FOUND)
    
    # Get last cycle number
    last_cycle = db.query(Cycle).filter(
        Cycle.group_id == group_id
    ).order_by(Cycle.cycle_number.desc()).first()
    
    cycle_number = (last_cycle.cycle_number + 1) if last_cycle else 1
    
    # Create new cycle
    from datetime import datetime, timedelta
    new_cycle = Cycle(
        group_id=group_id,
        cycle_number=cycle_number,
        beneficiary_id=next_beneficiary.user_id,
        status="active",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)  # Default 30 days
    )
    
    db.add(new_cycle)
    
    # Create contribution records for all members
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()
    
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        contribution = Contribution(
            cycle_id=new_cycle.id,
            user_id=member.user_id,
            amount=group.contribution_amount,
            phone_number=user.phone_number
        )
        db.add(contribution)
        
        # Create notification for member
        notification = Notification(
            user_id=member.user_id,
            title="New Cycle Started",
            message=f"Cycle {cycle_number} has started in {group.name}. Please contribute KES {group.contribution_amount:,.0f}"
        )
        db.add(notification)
    
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group_id}", status_code=status.HTTP_302_FOUND)


# Import at end to avoid circular imports
from app.models.models import Contribution
