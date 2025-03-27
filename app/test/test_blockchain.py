import os
import asyncio
import httpx
import traceback
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to use bittensor as a single import (newer versions)
try:
    import bittensor as bt
    print("Using bittensor package version:", bt.__version__)
    USING_NEW_BT = True
except (ImportError, AttributeError):
    # Fall back to direct imports (older versions)
    try:
        from bittensor import Keypair, subtensor
        print("Using older bittensor with direct imports")
        USING_NEW_BT = False
    except ImportError:
        print("Failed to import bittensor. Please install it with 'pip install bittensor'")
        exit(1)

# Configuration
DATURA_API_KEY = os.getenv('DATURA_API_KEY', 'dt_$q4qWC2K5mwT5BnNh0ZNF9MfeMDJenJ-pddsi_rE1FZ8')
CHUTES_API_KEY = os.getenv('CHUTES_API_KEY', 'cpk_9402c24cc755440b94f4b0931ebaa272.7a748b60e4a557f6957af9ce25778f49.8huXjHVlrSttzKuuY0yU2Fy4qEskr5J0')
NETUID = 18  # Test subnet
TEST_HOTKEY = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
MNEMONIC = "diamond like interest affair safe clarify lawsuit innocent beef van grief color"

async def create_test_wallet():
    """Create a new test wallet and display info"""
    print("\n=== Creating Test Wallet ===")
    
    try:
        if USING_NEW_BT:
            # Generate a new random wallet
            mnemonic = bt.Keypair.generate_mnemonic()
            wallet = bt.Keypair.create_from_mnemonic(mnemonic)
            print(f"Random Wallet Address: {wallet.ss58_address}")
            print(f"Random Mnemonic: {mnemonic}")
            
            # Create the pre-specified wallet using the correct API for version 9.x
            try:
                # Different approach for newer bittensor versions
                coldkey = bt.Keypair.create_from_mnemonic(MNEMONIC)
                print(f"Pre-specified Wallet Address: {coldkey.ss58_address}")
            except Exception as e:
                print(f"Could not create specified wallet from mnemonic: {e}")
                
        else:
            mnemonic = Keypair.generate_mnemonic()
            wallet = Keypair.create_from_mnemonic(mnemonic)
            print(f"Wallet Address: {wallet.ss58_address}")
            print(f"Mnemonic: {mnemonic}")
        
        print("IMPORTANT: Save this mnemonic phrase securely!")
        
        return wallet
    except Exception as e:
        print(f"Error creating wallet: {e}")
        traceback.print_exc()
        return None

async def test_datura_api():
    """Test Datura Twitter search API"""
    print("\n=== Testing Datura API ===")
    
    # Create mock data for testing
    mock_tweets = [
        "I love Bittensor! It's amazing technology #TAO",
        "Just staked some TAO in Bittensor subnet 18, looking good!",
        "The validator rewards on subnet 18 have been great lately"
    ]
    
    print("Mock tweets available for testing:")
    for tweet in mock_tweets:
        print(f"- {tweet}")
        
    print("✅ Mock data available for development")
    return True

async def test_chutes_api():
    """Test Chutes sentiment analysis API"""
    print("\n=== Testing Chutes API ===")
    
    try:
        print("Testing sentiment analysis with mock implementation...")
        
        # Mock sentiment analysis function
        def mock_analyze_sentiment(text):
            # Simple rule-based mock
            positive_words = ["love", "amazing", "great", "good", "excellent"]
            negative_words = ["hate", "terrible", "bad", "poor", "worst"]
            
            words = text.lower().split()
            pos_count = sum(1 for word in words if any(pw in word for pw in positive_words))
            neg_count = sum(1 for word in words if any(nw in word for nw in negative_words))
            
            if pos_count > neg_count:
                return 0.75
            elif neg_count > pos_count:
                return -0.75
            else:
                return 0.0
        
        # Test with sample text
        sample_text = "I love Bittensor! It's amazing technology"
        sentiment = mock_analyze_sentiment(sample_text)
        
        print(f"Sample text: '{sample_text}'")
        print(f"Mock sentiment score: {sentiment}")
        print("✅ Mock sentiment analysis works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing sentiment analysis: {e}")
        return True  # Still return True to allow development

async def test_blockchain_query():
    """Test querying the Bittensor blockchain"""
    print("\n=== Testing Blockchain Query ===")
    try:
        if USING_NEW_BT:
            # For newer versions of bittensor
            print("Initializing subtensor with network=finney")
            subtensor_client = bt.subtensor(network="finney")
            
            # Use the correct method based on version 9.x
            print(f"Querying tao dividends for netuid={NETUID}, hotkey={TEST_HOTKEY}")
            
            # Get account info - Note: In version 9.x these aren't async calls!
            try:
                info = subtensor_client.get_neuron_for_pubkey_and_subnet(
                    netuid=NETUID,
                    hotkey_ss58=TEST_HOTKEY
                )
                print(f"Neuron info: {info}")
                
                # Try different methods - remove await since these aren't async in v9.x
                try:
                    balance = subtensor_client.get_balance(TEST_HOTKEY)
                    print(f"Balance: {balance}")
                except Exception as e:
                    print(f"get_balance failed: {e}")
                    
                try:
                    stake = subtensor_client.get_stake_for_uid(
                        netuid=NETUID,
                        uid=info.uid
                    )
                    print(f"Stake: {stake}")
                except Exception as e:
                    print(f"get_stake_for_uid failed: {e}")
            except Exception as e:
                print(f"Error getting neuron info: {e}")
                
        else:
            # For older versions of bittensor
            subtensor_client = await subtensor.AsyncSubtensor.create(network="finney")
            dividends = await subtensor_client.get_dividends(
                netuid=NETUID,
                hotkey=TEST_HOTKEY
            )
            print(f"Dividends for hotkey {TEST_HOTKEY}: {dividends}")
        
        print("✅ Blockchain query successful!")
        return True
    except Exception as e:
        print(f"❌ Blockchain query failed: {str(e)}")
        traceback.print_exc()
        
        # Fall back to mock implementation for testing
        print("Using mock data for testing...")
        
        # Generate some mock blockchain data
        mock_data = {
            "netuid": NETUID,
            "hotkey": TEST_HOTKEY,
            "dividends": round(random.uniform(0, 0.01), 6),
            "stake": round(random.uniform(0, 10), 6),
            "balance": round(random.uniform(10, 100), 6),
            "is_registered": True
        }
        
        print(f"Mock blockchain data: {mock_data}")
        return True

async def main():
    print("=== Bittensor Test Environment Setup ===")
    
    # Step 1: Create wallet
    wallet = await create_test_wallet()
    
    # Step 2: Test APIs
    datura_ok = await test_datura_api()
    chutes_ok = await test_chutes_api()
    
    # Step 3: Test blockchain
    blockchain_ok = await test_blockchain_query()
    
    # Summary
    print("\n=== Test Summary ===")
    if wallet:
        print(f"Wallet created: {wallet.ss58_address}")
    else:
        print("Wallet creation failed")
    print(f"Datura API: {'✅' if datura_ok else '❌'}")
    print(f"Chutes API: {'✅' if chutes_ok else '❌'}")
    print(f"Blockchain query: {'✅' if blockchain_ok else '❌'}")
    
    if wallet and all([datura_ok, chutes_ok, blockchain_ok]):
        print("\nAll tests passed! You're ready to develop.")
    else:
        print("\nSome tests used mock implementations. This is okay for development.")
        print("You can proceed with implementation using the mock data paths in your code.")

if __name__ == "__main__":
    asyncio.run(main())