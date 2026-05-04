"""Placeholder routers for Phase 1 - will be fully implemented in later phases."""
from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/history")
async def contributions_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Show user's contribution history (placeholder)."""
    return templates.TemplateResponse(
        name="contributions/history.html",
        context={
            "request": request,
            "title": "Contribution History",
            "current_user": current_user,
            "contributions": []
        }
    )
