"""Placeholder routers for Phase 1 - will be fully implemented in later phases."""
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()


@router.get("/history")
async def payouts_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show user's payout history (placeholder)."""
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
