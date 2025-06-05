# Use Python 3.13 base image (slim for smaller size)
FROM python:3.13-slim

# Set environment vars to reduce prompts and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy web_server code into container
COPY . /app

# # Ensure access to shared `src/` code
# COPY ../src /app/src

# Install OS dependencies required by Flask, OAuth, and requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir Flask requests

# Expose the port Flask will use (should match docker-compose.yml)
EXPOSE 8000

# Run the app (adjust if your entrypoint changes)
CMD ["python", "login-server.py"]