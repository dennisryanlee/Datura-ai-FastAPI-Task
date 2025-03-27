from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class SentimentTaskHistory(Base):
    __tablename__ = "sentiment_task_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, index=True)
    netuid = Column(Integer)
    hotkey = Column(String(255))
    amount = Column(Float)
    sentiment_score = Column(Float, nullable=True)
    action = Column(String(20), nullable=True)  # "stake" or "unstake"
    status = Column(String(20), default="PENDING")  # PENDING, COMPLETED, FAILED
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class DividendQueryHistory(Base):
    __tablename__ = "dividend_query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(36), unique=True, index=True)
    netuid = Column(Integer)
    hotkey = Column(String(255))
    dividends = Column(Float, default=0.0)
    stake = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    cached = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
