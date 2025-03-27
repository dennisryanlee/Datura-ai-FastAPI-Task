from fastapi import Header, HTTPException, status, Depends
from typing import Optional, AsyncGenerator
from redis import Redis
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from typing import Generator
import redis
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User

def get_redis() -> Redis:
    """
    Get a Redis client instance
    """
    try:
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=False
        )
    except Exception as e:
        print(f"Redis connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_db() -> Generator:
    """
    Get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis_client() -> Redis:
    """
    Get Redis client.
    """
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    return redis_client

def get_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Validate API key.
    """
    # For development, accept any API key
    if api_key:
        return api_key
    
    # In production, validate against settings
    # if api_key == settings.API_KEY:
    #     return api_key
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user.
    """
    # For development, return mock user
    return {
        "id": 1,
        "email": "test@example.com",
        "is_active": True
    }

def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get current active user.
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user