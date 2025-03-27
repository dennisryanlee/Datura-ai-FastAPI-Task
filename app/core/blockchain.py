import random
import traceback
import asyncio
import os
import logging
import time
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Attempt to import AsyncSubtensor
try:
    from bittensor.core.async_subtensor import AsyncSubtensor
    from bittensor import wallet
    logger.info("Successfully imported AsyncSubtensor and wallet")
    BITTENSOR_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import AsyncSubtensor: {e}")
    BITTENSOR_AVAILABLE = False

class BitensorClient:
    _instance = None
    _wallet = None
    _subtensor = None
    _initialized = False
    _initialization_error = None
    
    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BitensorClient()
            await cls._instance._init()
        return cls._instance
    
    async def _init(self):
        """Initialize wallet and AsyncSubtensor"""
        if self._initialized:
            return
            
        try:
            if not BITTENSOR_AVAILABLE:
                self._initialization_error = "Bittensor library is not available"
                logger.error(self._initialization_error)
                self._initialized = True
                return
                
            logger.info("Initializing wallet...")
            # Initialize wallet with pre-specified mnemonic
            self._wallet = await self._initialize_wallet()
            if not self._wallet:
                self._initialization_error = "Failed to initialize wallet"
                logger.error(self._initialization_error)
                self._initialized = True
                return
                
            logger.info("Initializing AsyncSubtensor...")
            
            # Initialize AsyncSubtensor correctly - WITHOUT chain_endpoint parameter
            # First try direct initialization without async context
            try:
                # Direct initialization
                self._subtensor = AsyncSubtensor(network="finney")
                logger.info("AsyncSubtensor initialized with direct instantiation")
                
                # Test that it works
                await self._subtensor.get_block_hash()
                logger.info("AsyncSubtensor connection test successful")
                
            except Exception as e1:
                logger.error(f"Direct initialization failed: {e1}")
                try:
                    # Try using the create method if available
                    self._subtensor = await AsyncSubtensor.create(network="finney")
                    logger.info("AsyncSubtensor initialized with create() method")
                    
                    # Test that it works
                    await self._subtensor.get_block_hash()
                    logger.info("AsyncSubtensor connection test successful")
                    
                except Exception as e2:
                    logger.error(f"Create method failed too: {e2}")
                    self._subtensor = None
            
            logger.info("Bittensor client initialization completed successfully")
            self._initialized = True
            
        except Exception as e:
            self._initialization_error = f"Error during initialization: {e}"
            logger.error(self._initialization_error)
            traceback.print_exc()
            self._initialized = True
    
    async def _initialize_wallet(self):
        """Initialize wallet with the pre-specified mnemonic"""
        try:
            logger.info("Initializing wallet from mnemonic...")
            
            # Use the exact mnemonic specified in README
            mnemonic = os.getenv("WALLET_MNEMONIC", "diamond like interest affair safe clarify lawsuit innocent beef van grief color")
            
            # Create wallet instance
            wallet_obj = wallet(name="default", hotkey="default")
            
            # Set mnemonic
            wallet_obj.set_mnemonic(mnemonic=mnemonic)
            
            logger.info(f"Wallet initialized with coldkey: {wallet_obj.coldkeypub.ss58_address}")
            return wallet_obj
            
        except Exception as e:
            logger.error(f"Error initializing wallet: {e}")
            traceback.print_exc()
            return None
            
    async def get_dividends(self, netuid: int, hotkey: str = None) -> Dict[str, Any]:
        """
        Get TAO dividends for a specific hotkey and subnet
        """
        # Wait for initialization if it's still in progress
        if not self._initialized:
            await self._init()
            
        # Default hotkey if not provided
        if not hotkey:
            hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
            
        # Check if Bittensor is properly initialized
        if self._initialization_error or not self._subtensor:
            # Return mock data with the error
            error_msg = self._initialization_error or "Bittensor is not available or not initialized"
            logger.warning(f"Using mock data due to initialization error: {error_msg}")
            
            # Generate mock data including dummy sentiment info
            return {
                "netuid": netuid,
                "hotkey": hotkey,
                "dividends": 0.0,
                "stake": 0.0,
                "balance": 0.0,
                "is_registered": False,
                "cached": False,
                "error": error_msg,
                "using_mock_data": True
            }
        
        try:
            logger.info(f"Querying blockchain for dividends: netuid={netuid}, hotkey={hotkey}")
            
            # Get a consistent block hash for all queries
            block_hash = await self._subtensor.get_block_hash()
            
            # Get neuron info
            neuron = await self._subtensor.get_neuron_for_pubkey_and_subnet(
                hotkey_ss58=hotkey,
                netuid=netuid,
                block_hash=block_hash
            )
            
            # Get dividend information
            dividends = await self._subtensor.get_dividends_per_subnet(
                netuid=netuid,
                hotkey_ss58=hotkey,
                block_hash=block_hash
            )
            
            # Get balance
            balance = await self._subtensor.get_balance(
                address=hotkey,
                block_hash=block_hash
            )
            
            # Build response from real data
            stake = float(neuron.stake) if neuron else 0
            
            return {
                "netuid": netuid,
                "hotkey": hotkey,
                "dividends": float(dividends) if dividends is not None else 0.0,
                "stake": stake,
                "balance": float(balance) if balance is not None else 0.0,
                "is_registered": neuron is not None,
                "cached": False,
                "using_real_data": True
            }
                
        except Exception as e:
            logger.error(f"Error querying blockchain: {e}")
            traceback.print_exc()
            
            # Return fallback data with error information
            return {
                "netuid": netuid,
                "hotkey": hotkey,
                "dividends": 0.0,
                "stake": 0.0,
                "balance": 0.0,
                "is_registered": False,
                "cached": False,
                "error": str(e),
                "using_mock_data": True
            }
    
    async def stake_tao(self, netuid: int, hotkey: str, amount: float):
        """
        Stake TAO to a hotkey on a subnet using AsyncSubtensor with context manager
        """
        try:
            if not BITTENSOR_AVAILABLE or not self._wallet:
                raise ValueError("Bittensor is not available or wallet not initialized")
                
            logger.info(f"Staking {amount} TAO to hotkey {hotkey} on subnet {netuid}")
            
            async with await self._subtensor as subtensor:
                # Get current balance
                balance = await subtensor.get_balance(self._wallet.coldkeypub.ss58_address)
                logger.info(f"Current wallet balance: {balance}")
                
                if float(balance) < amount:
                    return {
                        "success": False,
                        "message": f"Insufficient balance: {balance} < {amount}",
                        "hotkey": hotkey,
                        "netuid": netuid
                    }
                
                # Execute stake
                stake_result = await subtensor.add_stake(
                    wallet=self._wallet,
                    hotkey_ss58=hotkey,
                    amount=amount,
                    wait_for_inclusion=True,
                    prompt=False
                )
                
                # Get updated neuron info
                neuron = await subtensor.get_neuron_for_pubkey_and_subnet(
                    hotkey_ss58=hotkey,
                    netuid=netuid
                )
                
                new_stake = float(neuron.stake) if neuron else 0
                
                return {
                    "success": True,
                    "message": f"Successfully staked {amount} TAO to {hotkey}",
                    "tx_hash": stake_result.hash_hex if hasattr(stake_result, 'hash_hex') else "unknown",
                    "new_stake": new_stake,
                    "hotkey": hotkey,
                    "netuid": netuid
                }
                
        except Exception as e:
            logger.error(f"Error during staking: {e}")
            traceback.print_exc()
            
            return {
                "success": False,
                "message": f"Staking error: {str(e)}",
                "hotkey": hotkey,
                "netuid": netuid
            }
    
    async def unstake_tao(self, netuid: int, hotkey: str, amount: float):
        """
        Unstake TAO from a hotkey on a subnet using AsyncSubtensor with context manager
        """
        try:
            if not BITTENSOR_AVAILABLE or not self._wallet:
                raise ValueError("Bittensor is not available or wallet not initialized")
                
            logger.info(f"Unstaking {amount} TAO from hotkey {hotkey} on subnet {netuid}")
            
            async with await self._subtensor as subtensor:
                # Get current stake
                neuron = await subtensor.get_neuron_for_pubkey_and_subnet(
                    hotkey_ss58=hotkey, 
                    netuid=netuid
                )
                
                if not neuron:
                    return {
                        "success": False,
                        "message": f"Neuron not found for hotkey {hotkey} on subnet {netuid}",
                        "hotkey": hotkey,
                        "netuid": netuid
                    }
                
                current_stake = float(neuron.stake)
                logger.info(f"Current stake: {current_stake}")
                
                if current_stake < amount:
                    return {
                        "success": False,
                        "message": f"Insufficient stake: {current_stake} < {amount}",
                        "hotkey": hotkey,
                        "netuid": netuid
                    }
                
                # Execute unstake
                unstake_result = await subtensor.unstake(
                    wallet=self._wallet,
                    hotkey=hotkey,
                    amount=amount,
                    wait_for_inclusion=True,
                    prompt=False
                )
                
                # Get updated neuron info
                updated_neuron = await subtensor.get_neuron_for_pubkey_and_subnet(
                    hotkey_ss58=hotkey,
                    netuid=netuid
                )
                
                new_stake = float(updated_neuron.stake) if updated_neuron else 0
                
                return {
                    "success": True,
                    "message": f"Successfully unstaked {amount} TAO from {hotkey}",
                    "tx_hash": unstake_result.hash_hex if hasattr(unstake_result, 'hash_hex') else "unknown",
                    "old_stake": current_stake,
                    "new_stake": new_stake,
                    "hotkey": hotkey,
                    "netuid": netuid
                }
                
        except Exception as e:
            logger.error(f"Error during unstaking: {e}")
            traceback.print_exc()
            
            return {
                "success": False,
                "message": f"Unstaking error: {str(e)}",
                "hotkey": hotkey,
                "netuid": netuid
            }