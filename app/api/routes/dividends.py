from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import traceback
import uuid

from app.core.auth import get_api_key
from app.db.database import get_db
from app.core.blockchain import BitensorClient
from app.worker import analyze_sentiment_and_stake
from app.services.cache import RedisCache
from app.db.models import DividendQueryHistory
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/tao_dividends", summary="Get TAO dividends")
async def get_tao_dividends(
    netuid: int = Query(1, description="Network UID"),
    hotkey: Optional[str] = Query(None, description="Hotkey address"),
    trade: bool = Query(False, description="Whether to analyze sentiment and stake"),
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(RedisCache),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the TAO dividends for a specific netuid and hotkey.
    """
    try:
        print("Recording dividend query in database")
        is_cached = False
        
        # Try to get from cache first if trade is not requested
        if not trade:
            cache_key = f"dividends:{netuid}:{hotkey or 'default'}"
            cached_data = await cache.get(cache_key)
            
            if cached_data:
                # Add cached flag and return
                cached_data["cached"] = True
                is_cached = True
                
                # Record this cached query in the database
                print(f"Recording cached query for {netuid}:{hotkey}")
                query_record = DividendQueryHistory(
                    query_id=str(uuid.uuid4()),
                    netuid=netuid,
                    hotkey=hotkey or "default",
                    dividends=cached_data.get("dividends", 0.0),
                    stake=cached_data.get("stake", 0.0),
                    balance=cached_data.get("balance", 0.0),
                    cached=True
                )
                db.add(query_record)
                await db.commit()
                print(f"Record added successfully: {query_record.query_id}")
                
                return cached_data
        
        # Get data from blockchain
        client = await BitensorClient.get_instance()
        result = await client.get_dividends(netuid=netuid, hotkey=hotkey)
        
        # Add default fields
        result["cached"] = False
        result["stake_tx_triggered"] = False
        
        # If trade requested, trigger background task
        if trade:
            # Calculate a default amount if not provided (e.g., 10% of balance up to 10 TAO)
            default_amount = min(10.0, result.get("balance", 0) * 0.1)
            
            # Make sure to pass the amount parameter
            task = analyze_sentiment_and_stake.delay(
                netuid=netuid,
                hotkey=hotkey or "default_hotkey",
                amount=default_amount  # Make sure this parameter is included
            )
            
            result["task_id"] = task.id
            result["stake_tx_triggered"] = True
        else:
            # Cache the result for non-trade requests
            await cache.set(f"dividends:{netuid}:{hotkey or 'default'}", result)
        
        # Record this fresh query in the database
        print(f"Recording fresh query for {netuid}:{hotkey}")
        query_record = DividendQueryHistory(
            query_id=str(uuid.uuid4()),
            netuid=netuid,
            hotkey=hotkey or "default",
            dividends=result.get("dividends", 0.0),
            stake=result.get("stake", 0.0),
            balance=result.get("balance", 0.0),
            cached=is_cached
        )
        db.add(query_record)
        await db.commit()
        print(f"Record added successfully: {query_record.query_id}")
        
        return result
    
    except Exception as e:
        # Add detailed error logging
        print(f"Error in tao_dividends: {e}")
        print(traceback.format_exc())
        
        # Try to rollback the database session if there was an error during the commit
        try:
            await db.rollback()
        except:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying blockchain: {str(e)}"
        )

@router.get("/test_db", summary="Test database insertion")
async def test_db(
    api_key: str = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Test database insertion"""
    try:
        # Create a test record
        query_record = DividendQueryHistory(
            query_id=str(uuid.uuid4()),
            netuid=1,
            hotkey="test_hotkey",
            dividends=123.45,
            stake=67.89,
            balance=1000.0,
            cached=False
        )
        db.add(query_record)
        await db.commit()
        
        return {"message": "Test record inserted successfully", "query_id": query_record.query_id}
    except Exception as e:
        print(f"Error in test_db: {e}")
        print(traceback.format_exc())
        
        try:
            await db.rollback()
        except:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )