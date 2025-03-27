from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class TaoDividendsResponse(BaseModel):
    netuid: int
    hotkey: str
    dividends: float = 0.0
    stake: float = 0.0
    balance: float = 0.0
    is_registered: bool = False
    cached: bool = False
    sentiment_score: Optional[float] = None
    stake_tx_triggered: Optional[bool] = None
    task_id: Optional[str] = None
    error: Optional[str] = None
    mock_data: Optional[bool] = None
    
    class Config:
        orm_mode = True

class DividendQueryHistoryCreate(BaseModel):
    query_id: str
    netuid: int
    hotkey: str
    dividends: float = 0.0
    stake: float = 0.0
    balance: float = 0.0
    cached: bool = False

class DividendQueryHistoryResponse(DividendQueryHistoryCreate):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
