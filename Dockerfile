FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY gunicorn_config.py .

# Create necessary directories
RUN mkdir -p chroma logs .rag_settings _temp .rag_cache .rag_history .rag_monitoring

# Expose port
EXPOSE 8080

# Default to production mode (can be overridden)
ENV FLASK_DEBUG=False
ENV API_HOST=0.0.0.0
ENV API_PORT=8080
ENV PYTHONUNBUFFERED=1

# Start with Gunicorn (production) or Flask dev server (development)
CMD ["sh", "-c", "if [ \"$FLASK_DEBUG\" = \"True\" ]; then python3 -m flask --app src.app run --host=0.0.0.0 --port=8080 --reload; else gunicorn -c gunicorn_config.py src.app:app; fi"]

