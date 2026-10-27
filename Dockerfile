FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# CPU-only torch keeps the image far smaller than the default CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Install app-store-scraper separately (it hard-pins requests==2.23.0 which conflicts)
RUN pip install --no-cache-dir --no-deps app-store-scraper==0.3.5

# Run as a non-root user (uid 1000): required by Hugging Face Spaces, harmless elsewhere
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
WORKDIR /home/user/app

# Pre-download embedding model to prevent startup timeouts
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
# Copy source code and data stores (writable by the app user: Chroma writes to its sqlite file)
COPY --chown=user pipeline/ pipeline/
COPY --chown=user server/ server/
COPY --chown=user data/ data/

# Set env to production
ENV PYTHONUNBUFFERED=1

# Run FastAPI server
# Hugging Face Spaces serves port 7860; Railway/others inject PORT
ENV PORT=7860
EXPOSE 7860
CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT}
