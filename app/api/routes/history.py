from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.core.deps import get_current_active_user, get_db
from app.schemas.dividend_schemas import DividendQueryHistoryResponse
from app.schemas.task_schemas import SentimentTaskResponse
from app.db.models import DividendQueryHistory, SentimentTaskHistory
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/dividend-history", response_model=List[DividendQueryHistoryResponse])
def get_dividend_history(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get history of dividend queries"""
    history = db.query(DividendQueryHistory).order_by(
        DividendQueryHistory.created_at.desc()
    ).offset(skip).limit(limit).all()
    return history

@router.get("/task-history", response_model=List[SentimentTaskResponse])
def get_task_history(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get history of sentiment analysis tasks"""
    query = db.query(SentimentTaskHistory).order_by(
        SentimentTaskHistory.created_at.desc()
    )
    
    if status:
        query = query.filter(SentimentTaskHistory.status == status)
        
    tasks = query.offset(skip).limit(limit).all()
    return tasks
