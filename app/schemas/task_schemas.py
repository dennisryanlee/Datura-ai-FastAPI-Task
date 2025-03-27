from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class TaskStatusBase(BaseModel):
    task_id: str
    status: str
    
class TaskStatusResponse(TaskStatusBase):
    result: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class SentimentTaskCreate(BaseModel):
    task_id: str
    netuid: int
    hotkey: str
    amount: Optional[float] = None
    sentiment_score: Optional[float] = None
    action: Optional[str] = None
    status: str = "PENDING"
    
class SentimentTaskResponse(SentimentTaskCreate):
    id: int
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
