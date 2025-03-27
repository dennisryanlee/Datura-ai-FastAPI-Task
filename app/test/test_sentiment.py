import pytest
from app.services.sentiment import SentimentAnalyzer

@pytest.mark.asyncio
async def test_get_mock_tweets():
    """Test mock tweets generation"""
    analyzer = SentimentAnalyzer()
    tweets = await analyzer.get_tweets_about_subnet(18)
    
    assert "tweets" in tweets
    assert len(tweets["tweets"]) > 0
    assert "text" in tweets["tweets"][0]
    assert "Bittensor" in tweets["tweets"][0]["text"]

@pytest.mark.asyncio
async def test_analyze_sentiment():
    """Test sentiment analysis"""
    analyzer = SentimentAnalyzer()
    
    # Create mock tweets
    mock_tweets = {
        "tweets": [
            {"text": "Bittensor is amazing! Best project ever! #TAO"},
            {"text": "Just staked more TAO. Super excited about the future!"}
        ]
    }
    
    sentiment = await analyzer.analyze_sentiment(mock_tweets)
    
    # Sentiment should be between -100 and 100
    assert -100 <= sentiment <= 100
