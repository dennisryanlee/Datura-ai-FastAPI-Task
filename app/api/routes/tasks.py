from fastapi import APIRouter, HTTPException, Depends, status, Query
from app.core.auth import get_api_key
from app.core.config import settings
import redis
import json

router = APIRouter()

@router.get("/{task_id}")
async def get_task_by_id(task_id: str, api_key: str = Depends(get_api_key)):
    """
    Get the status of a background task
    
    Args:
        task_id: The ID of the task to check
        api_key: API key for authentication
        
    Returns:
        dict: Current status of the task
    """
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        # Get task status from Redis
        status_key = f"task_status:{task_id}"
        status_data = redis_client.get(status_key)
        
        if not status_data:
            # Try to get from Celery result backend
            from app.worker import celery_app
            task = celery_app.AsyncResult(task_id)
            
            if task.state == 'PENDING':
                return {
                    "task_id": task_id,
                    "status": "PENDING",
                    "message": "Task is waiting to be processed"
                }
            elif task.state == 'FAILURE':
                return {
                    "task_id": task_id,
                    "status": "FAILED",
                    "message": str(task.info)
                }
            else:
                return {
                    "task_id": task_id,
                    "status": task.state,
                    "result": task.result if task.state == 'SUCCESS' else None
                }
        
        # Parse the status data
        status_info = json.loads(status_data)
        
        return {
            "task_id": task_id,
            "status": status_info.get("status", "UNKNOWN"),
            "updated_at": status_info.get("updated_at"),
            "data": status_info.get("data")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task status: {str(e)}"
        )

@router.get("/status")
async def get_task_status(
    task_id: str = Query(..., description="Task ID to check status"),
    api_key: str = Depends(get_api_key)
):
    """
    Get status of a background task.
    """
    # For development, return mock data
    return {
        "task_id": task_id,
        "status": "COMPLETED",
        "result": {
            "sentiment_score": 0.75,
            "action": "STAKE",
            "netuid": 18,
            "hotkey": "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v",
            "mock_data": True
        }
    }