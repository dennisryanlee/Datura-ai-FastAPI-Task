from celery import Celery
import redis
import json
import os
import asyncio
from time import sleep
import datetime
import traceback
import time
import random

from app.services.sentiment import SentimentAnalyzer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import bittensor
from bittensor import wallet
from bittensor import subtensor

# Create database engine for worker
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Initialize Redis client for task status tracking
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

# Initialize Celery app
celery_app = Celery(
    "bittensor_app",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
)

def update_task_status(task_id, status, message=None):
    """
    Update the status of a task in Redis
    
    Args:
        task_id: The task ID
        status: The new status
        message: Optional message with details
    """
    task_data = {
        'task_id': task_id,
        'status': status,
        'updated_at': time.time()
    }
    
    if message:
        task_data['message'] = message
    
    # Store in Redis
    try:
        redis_client.setex(
            f'task_status:{task_id}',
            settings.TASK_STATUS_TTL,
            json.dumps(task_data)
        )
    except Exception as e:
        print(f"Error updating task status: {e}")

async def analyze_sentiment(netuid):
    """
    Analyze Twitter sentiment for a subnet using SentimentAnalyzer service
    """
    analyzer = SentimentAnalyzer()
    try:
        sentiment_score = await analyzer.analyze_sentiment_for_subnet(netuid)
        print(f"Analyzed sentiment for netuid {netuid}: {sentiment_score:.2f}")
        return sentiment_score
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        # Fallback to mock if there's an error
        random.seed(netuid)
        mock_score = random.uniform(-1, 1)
        print(f"Using mock sentiment score: {mock_score:.2f}")
        return mock_score

async def record_task_status(task_id, netuid, hotkey, sentiment_score, action, amount, status, error=None):
    """Record task status in database"""
    # Import here to avoid circular imports
    from app.db.models import SentimentTaskHistory
    
    async with async_session() as session:
        try:
            # Check if task already exists
            from sqlalchemy import select
            query = select(SentimentTaskHistory).filter(SentimentTaskHistory.task_id == task_id)
            result = await session.execute(query)
            existing_task = result.scalars().first()
            
            if existing_task:
                # Update existing task
                existing_task.status = status
                existing_task.sentiment_score = sentiment_score
                existing_task.action = action
                existing_task.amount = amount
                existing_task.error = error
                existing_task.completed_at = datetime.datetime.utcnow() if status in ["COMPLETED", "FAILED"] else None
            else:
                # Create new task record
                task = SentimentTaskHistory(
                    task_id=task_id,
                    netuid=netuid,
                    hotkey=hotkey,
                    sentiment_score=sentiment_score,
                    action=action,
                    amount=amount,
                    status=status,
                    error=error,
                    completed_at=datetime.datetime.utcnow() if status in ["COMPLETED", "FAILED"] else None
                )
                session.add(task)
            
            await session.commit()
            print(f"Recorded task {task_id} with status {status} in database")
            
        except Exception as e:
            print(f"Error recording task status: {e}")
            print(traceback.format_exc())
            await session.rollback()

@celery_app.task(bind=True)
def analyze_sentiment_and_stake(self, netuid, hotkey, amount):
    """
    Analyze Twitter sentiment for a subnet and stake/unstake based on the result
    """
    task_id = self.request.id
    
    try:
        # Update status to PROCESSING
        update_task_status(task_id, "PROCESSING", f"Processing sentiment analysis for netuid {netuid}")
        
        # Create event loop for async operations
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Update status to ANALYZING_SENTIMENT
        update_task_status(task_id, "ANALYZING_SENTIMENT", "Analyzing Twitter sentiment")
        
        # Call the sentiment analysis function using run_until_complete
        sentiment_score = loop.run_until_complete(analyze_sentiment(netuid))
        
        # Record current step in database
        loop.run_until_complete(record_task_status(
            task_id=task_id,
            netuid=netuid,
            hotkey=hotkey,
            sentiment_score=sentiment_score,
            action=None,  # Not determined yet
            amount=amount,
            status="ANALYZING_SENTIMENT"
        ))
        
        # Determine action based on sentiment
        action = "stake" if sentiment_score > 0.2 else "unstake"
        
        # Update status to CONNECTING_BLOCKCHAIN
        update_task_status(task_id, "CONNECTING_BLOCKCHAIN", f"Connecting to blockchain to {action}")
        
        # Record updated action in database
        loop.run_until_complete(record_task_status(
            task_id=task_id,
            netuid=netuid,
            hotkey=hotkey,
            sentiment_score=sentiment_score,
            action=action,
            amount=amount,
            status="CONNECTING_BLOCKCHAIN"
        ))
        
        # Execute stake or unstake based on sentiment
        if action == "stake":
            # Use mock staking implementation
            blockchain_result = loop.run_until_complete(mock_stake_tao(netuid, hotkey, amount))
        else:
            # Use mock unstaking implementation
            blockchain_result = loop.run_until_complete(mock_unstake_tao(netuid, hotkey, amount))
        
        # Check if operation was successful
        if blockchain_result.get("success", False):
            # Update status to COMPLETED
            update_task_status(task_id, "COMPLETED", blockchain_result.get("message", f"Successfully completed {action} operation"))
            
            # Record successful completion in database
            loop.run_until_complete(record_task_status(
                task_id=task_id,
                netuid=netuid,
                hotkey=hotkey,
                sentiment_score=sentiment_score,
                action=action,
                amount=amount,
                status="COMPLETED"
            ))
        else:
            # Update status to FAILED
            error_message = blockchain_result.get("message", f"Failed to {action}")
            update_task_status(task_id, "FAILED", error_message)
            
            # Record failure in database
            loop.run_until_complete(record_task_status(
                task_id=task_id,
                netuid=netuid,
                hotkey=hotkey,
                sentiment_score=sentiment_score,
                action=action,
                amount=amount,
                status="FAILED",
                error=error_message
            ))
            
            # Raise exception to mark task as failed
            raise ValueError(error_message)
        
        # Return complete result
        result = {
            "task_id": task_id,
            "status": "COMPLETED",
            "netuid": netuid,
            "hotkey": hotkey,
            "amount": amount,
            "sentiment_score": sentiment_score,
            "action": action,
            "blockchain_result": blockchain_result
        }
        
        return result
        
    except Exception as e:
        # Update status to FAILED
        error_message = f"Task failed: {str(e)}"
        update_task_status(task_id, "FAILED", error_message)
        
        # Log error for debugging
        print(f"Error in analyze_sentiment_and_stake: {e}")
        print(traceback.format_exc())
        
        # Try to record failure in database
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            loop.run_until_complete(record_task_status(
                task_id=task_id,
                netuid=netuid,
                hotkey=hotkey,
                sentiment_score=None,  # May not have gotten to this point
                action=None,           # May not have determined this
                amount=amount,
                status="FAILED",
                error=str(e)
            ))
        except Exception as db_error:
            print(f"Error recording task failure: {db_error}")
        
        raise

async def stake_tao(netuid, hotkey, amount):
    """
    Stake TAO to a hotkey on the Bittensor blockchain
    """
    try:
        print(f"Staking {amount} TAO to hotkey {hotkey} on subnet {netuid}")
        
        # Import bittensor modules within the function to avoid conflicts
        # This prevents naming conflicts with local variables
        import bittensor as bt
        
        # Create wallet - note we use bt.wallet (not bittensor.wallet)
        wallet_obj = bt.wallet(
            name="default",
            hotkey="default",
            path="./wallet"
        )
        
        # Load from mnemonic
        wallet_obj.set_mnemonic(
            mnemonic="diamond like interest affair safe clarify lawsuit innocent beef van grief color"
        )
        
        # Initialize subtensor connection
        subtensor_obj = bt.subtensor(
            network="finney",  # Use appropriate network
            chain_endpoint="ws://test.finney.opentensor.ai:9944"
        )
        
        # Check wallet balance before staking
        balance = subtensor_obj.get_balance(wallet_obj.coldkeypub.ss58_address)
        print(f"Wallet balance before staking: {balance}")
        
        if balance < amount:
            raise ValueError(f"Insufficient balance: {balance} < {amount}")
        
        # Execute stake with retry
        for attempt in range(3):  # Try up to 3 times
            try:
                print(f"Staking attempt {attempt+1}/3...")
                # Execute stake
                stake_result = subtensor_obj.add_stake(
                    wallet=wallet_obj,
                    hotkey_ss58=hotkey,
                    amount=amount,
                    wait_for_inclusion=True,
                    prompt=False
                )
                
                # If successful, break the retry loop
                if stake_result and stake_result.success:
                    break
            except Exception as retry_error:
                print(f"Attempt {attempt+1} failed: {retry_error}")
                if attempt < 2:  # If not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise  # Re-raise on last attempt
        
        # Check if the operation was successful
        if stake_result and stake_result.success:
            # Check new stake amount
            neuron = subtensor_obj.get_neuron_for_pubkey_and_subnet(
                hotkey_ss58=hotkey, 
                netuid=netuid
            )
            new_stake = neuron.stake if neuron else 0
            
            return {
                "success": True,
                "message": f"Successfully staked {amount} TAO to {hotkey}",
                "tx_hash": stake_result.hash_hex if hasattr(stake_result, 'hash_hex') else "unknown",
                "new_stake": new_stake,
                "hotkey": hotkey,
                "netuid": netuid
            }
        else:
            error_msg = "Staking failed" if stake_result else "No result returned"
            if stake_result and hasattr(stake_result, 'error_message'):
                error_msg = f"Staking failed: {stake_result.error_message}"
                
            return {
                "success": False,
                "message": error_msg,
                "hotkey": hotkey,
                "netuid": netuid
            }
    
    except Exception as e:
        print(f"Error during staking operation: {e}")
        print(traceback.format_exc())
        
        # Fall back to mock implementation for testing
        print("Falling back to mock implementation...")
        return await mock_stake_tao(netuid, hotkey, amount)

async def unstake_tao(netuid, hotkey, amount):
    """
    Unstake TAO from a hotkey on the Bittensor blockchain using real Bittensor functions
    
    Args:
        netuid: Network UID of the subnet
        hotkey: Hotkey SS58 address to unstake from
        amount: Amount of TAO to unstake
        
    Returns:
        dict: Result of the unstaking operation
    """
    try:
        print(f"Unstaking {amount} TAO from hotkey {hotkey} on subnet {netuid}")
        
        # Import bittensor correctly - import it here to avoid naming conflicts
        import bittensor as bt
        
        # Create wallet - use the correct API based on your version
        wallet_obj = bt.wallet(
            name="default",
            hotkey="default"
        )
        
        # Set the mnemonic (this is the correct way to load from mnemonic)
        wallet_obj.set_mnemonic(
            mnemonic="diamond like interest affair safe clarify lawsuit innocent beef van grief color"
        )
        
        # Initialize subtensor with the correct network
        subtensor_obj = bt.subtensor(
            network="finney",
            chain_endpoint="ws://test.finney.opentensor.ai:9944"
        )
        
        # Get current stake before unstaking
        current_stake = subtensor_obj.get_stake(
            hotkey_ss58=hotkey,
            coldkey_ss58=wallet_obj.coldkeypub.ss58_address,
            netuid=netuid
        )
        print(f"Current stake for hotkey {hotkey}: {current_stake}")
        
        if float(current_stake) < amount:
            raise ValueError(f"Insufficient stake: {current_stake} < {amount}")
        
        # Execute unstake with retry logic
        for attempt in range(3):  # Try up to 3 times
            try:
                print(f"Unstaking attempt {attempt+1}/3...")
                
                # Execute unstake with the correct parameters
                unstake_result = subtensor_obj.unstake(
                    wallet=wallet_obj,
                    hotkey=hotkey,  # This should be the hotkey address
                    netuid=netuid,
                    amount=amount  # Use the correct parameter name
                )
                
                # If we get here without exception, the operation succeeded
                break
                
            except Exception as retry_error:
                print(f"Attempt {attempt+1} failed: {retry_error}")
                if attempt < 2:  # If not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise  # Re-raise on last attempt
        
        # Check new stake after operation
        new_stake = subtensor_obj.get_stake(
            hotkey_ss58=hotkey,
            coldkey_ss58=wallet_obj.coldkeypub.ss58_address,
            netuid=netuid
        )
        print(f"New stake for hotkey {hotkey}: {new_stake}")
        
        # Determine if operation was successful by comparing stakes
        stake_decreased = float(new_stake) < float(current_stake)
        
        if stake_decreased:
            return {
                "success": True,
                "message": f"Successfully unstaked {amount} TAO from {hotkey}",
                "old_stake": float(current_stake),
                "new_stake": float(new_stake),
                "difference": float(current_stake) - float(new_stake),
                "hotkey": hotkey,
                "netuid": netuid
            }
        else:
            return {
                "success": False,
                "message": f"Unstaking operation did not decrease stake as expected",
                "old_stake": float(current_stake),
                "new_stake": float(new_stake),
                "hotkey": hotkey,
                "netuid": netuid
            }
    
    except Exception as e:
        print(f"Error during unstaking operation: {e}")
        print(traceback.format_exc())
        
        # Fall back to mock implementation for testing
        print("Falling back to mock implementation...")
        return await mock_unstake_tao(netuid, hotkey, amount)

async def mock_stake_tao(netuid, hotkey, amount):
    """
    Mock implementation for staking TAO
    """
    print(f"MOCK: Staking {amount} TAO to hotkey {hotkey} on subnet {netuid}")
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    # Return success response
    return {
        "success": True,
        "message": f"Successfully staked {amount} TAO to {hotkey} (MOCK)",
        "tx_hash": "0x" + "".join([random.choice("0123456789abcdef") for _ in range(64)]),
        "new_stake": amount,
        "hotkey": hotkey,
        "netuid": netuid
    }

async def mock_unstake_tao(netuid, hotkey, amount):
    """
    Mock implementation for unstaking TAO
    """
    print(f"MOCK: Unstaking {amount} TAO from hotkey {hotkey} on subnet {netuid}")
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    # Return success response
    return {
        "success": True,
        "message": f"Successfully unstaked {amount} TAO from {hotkey} (MOCK)",
        "tx_hash": "0x" + "".join([random.choice("0123456789abcdef") for _ in range(64)]),
        "new_stake": 0,
        "hotkey": hotkey,
        "netuid": netuid
    }