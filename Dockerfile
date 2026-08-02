FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data stores
COPY pipeline/ pipeline/
COPY server/ server/
COPY data/ data/

# Set env to production
ENV PYTHONUNBUFFERED=1

# Run FastAPI server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
