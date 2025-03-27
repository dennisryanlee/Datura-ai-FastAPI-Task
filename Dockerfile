FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including Rust toolchain properly
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    curl \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust properly with PATH setup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Verify Rust installation
RUN cargo --version

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make directory for wallet
RUN mkdir -p /wallet

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]