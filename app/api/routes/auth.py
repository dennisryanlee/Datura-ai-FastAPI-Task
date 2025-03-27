from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    Simple mock login endpoint that returns a token.
    """
    # For development purposes only - in production, validate against database
    if form_data.username == "test@example.com" and form_data.password == "password":
        # Return a mock token
        return {
            "access_token": "mock_token_for_development_only",
            "token_type": "bearer"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(username: str, password: str) -> Dict[str, Any]:
    """
    Simple mock registration endpoint.
    """
    # This is a placeholder - in production, create a user in database
    return {
        "message": "User registered successfully",
        "username": username
    }
