# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables for safety and behavior
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set working directory
WORKDIR /app

# Copy the entire chatbot source code into the container
COPY . /app

# Install system-level dependencies (if needed by psycopg2 or similar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Optionally copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port if needed (optional for a bot, which uses polling or webhook)
# EXPOSE 8443  # example port if you do webhooks

# Default run command
CMD ["python", "main.py"]