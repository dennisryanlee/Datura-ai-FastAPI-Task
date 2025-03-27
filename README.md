# Datura-ai FastAPI Task

A FastAPI-based API for interacting with Bittensor blockchain, performing sentiment analysis on Twitter data via Datura.ai, and automated staking/unstaking based on sentiment scores.

## 📋 Features

- 📊 **Blockchain Integration**: Get TAO dividends for specific subnets and hotkeys
- 🔍 **Sentiment Analysis**: Analyze Twitter sentiment for Bittensor subnets using Datura.ai
- 🤖 **Automated Staking**: Stake or unstake TAO based on sentiment analysis
- 💾 **Database Storage**: Track query and task history in PostgreSQL
- 🔄 **Caching**: Redis-based caching for performance optimization
- 🔒 **Authentication**: API key authentication for secure access

## 🛠️ Tech Stack

- **FastAPI**: Web framework for building APIs
- **Celery**: Distributed task queue for background processing
- **Redis**: Caching and message broker
- **PostgreSQL**: Database storage
- **Docker**: Containerization for easy deployment
- **Bittensor**: Blockchain interaction
- **Datura API**: For fetching tweets
- **Chutes API**: For sentiment analysis

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- A Bittensor wallet and mnemonic
- API keys for Datura and Chutes

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dennisryanlee/Datura-ai-FastAPI-Task.git
cd Datura-ai-FastAPI-Task
```

2. Create a `.env` file with the following content (replace with your actual keys):

```
API_KEY=your_api_key_here
DATURA_API_KEY=your_datura_api_key_here
CHUTES_API_KEY=your_chutes_api_key_here
USE_SEED=true
SEED_PHRASE=your seed phrase here
SUBTENSOR_NETWORK=testnet
SUBTENSOR_URL=ws://test.finney.opentensor.ai:9944
DEFAULT_NETUID=18
DEFAULT_HOTKEY=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v
```

3. Create a wallet directory:
```bash
mkdir -p wallet
```

4. Build and start the containers:
```bash
docker-compose up --build -d
```

5. Create the database:
```bash
docker-compose exec db psql -U postgres -c "CREATE DATABASE bittensor_db;"
```

6. Initialize database tables:
```bash
docker-compose exec api python -c "from app.db.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tao/tao_dividends` | GET | Get TAO dividends for a subnet and hotkey |
| `/api/v1/tasks/{task_id}` | GET | Get status of a background task |
| `/api/v1/history/query-history` | GET | Get history of dividend queries |
| `/api/v1/history/task-history` | GET | Get history of sentiment analysis tasks |
| `/api/v1/tao/test_blockchain_integration` | POST | Test blockchain staking/unstaking |
| `/health` | GET | API health check endpoint |

## 🧪 Example Usage

### Get TAO Dividends

```bash
curl -H "X-API-Key: your_api_key" "http://localhost:8000/api/v1/tao/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
```

### Get TAO Dividends and Perform Sentiment Analysis

```bash
curl -H "X-API-Key: your_api_key" "http://localhost:8000/api/v1/tao/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v&trade=true"
```

### Check Task Status

```bash
curl -H "X-API-Key: your_api_key" "http://localhost:8000/api/v1/tasks/your_task_id"
```

### View Query History

```bash
curl -H "X-API-Key: your_api_key" "http://localhost:8000/api/v1/history/query-history"
```

### View Task History

```bash
curl -H "X-API-Key: your_api_key" "http://localhost:8000/api/v1/history/task-history"
```

## 📊 Project Structure

```
Datura-ai-FastAPI-Task/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── routes/
│   │   │   ├── dividends.py
│   │   │   ├── history.py
│   │   │   └── tasks.py
│   │   ├── core/
│   │   │   ├── auth.py
│   │   │   ├── blockchain.py
│   │   │   └── config.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── services/
│   │   │   ├── cache.py
│   │   │   └── sentiment.py
│   │   ├── test/
│   │   │   ├── test_api.py
│   │   │   ├── test_blockchain.py
│   │   │   └── test_sentiment.py
│   │   ├── main.py
│   │   └── worker.py
│   ├── wallet/                 # Wallet directory (created at runtime)
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .gitignore
│   └── README.md
```

## ⚙️ Architecture

The application is composed of several Docker containers:
- **API server**: FastAPI application handling HTTP requests
- **Celery worker**: Processing background tasks like sentiment analysis
- **Redis**: Used for caching and as a message broker for Celery
- **PostgreSQL**: Database for storing query and task history

## 🧩 Features to be Implemented

- Advanced error handling and retry mechanisms
- Comprehensive logging system
- User authentication and multi-user support
- Dashboard for visualizing sentiment trends
- Batch processing for multiple operations
- Webhook notifications for task completion


## 🙏 Acknowledgements

- [Bittensor](https://bittensor.com) community
- [Datura.ai](https://datura.ai) for Twitter data
- [Chutes.ai](https://chutes.ai) for sentiment analysis
- All open-source libraries used in this project

Watch the application in action:

- https://www.screencapture.com/915483d9-8828-4b1b-b96c-19ae0d5d3e0b
- https://www.screencapture.com/a5f740bc-0423-4363-abae-ffd6634b7062
- https://www.screencapture.com/f4f37ca2-3ac5-4b48-ad84-48e4efcdf565
