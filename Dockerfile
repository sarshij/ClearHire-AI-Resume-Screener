# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Tesseract, OpenCV, Poppler (pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies (includes asyncpg for PostgreSQL)
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for NLP features
RUN python -m spacy download en_core_web_md --quiet 2>/dev/null || echo "Warning: Could not download spaCy model. NLP features will use fallback methods."

# Create necessary directories (data dir no longer needed – PostgreSQL is external)
RUN mkdir -p logs scratch

# Copy the current directory contents into the container at /app
COPY . .

# ── PostgreSQL connection (override at runtime via docker run -e or docker-compose) ──
ENV POSTGRES_HOST=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=resume_screener
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=

# Ensure the app user has permissions to write (needed for SQLite fallback on HF Spaces)
RUN chmod -R 777 /app

# Expose port 7860 as required by Hugging Face Spaces
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
