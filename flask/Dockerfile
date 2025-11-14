# Flask Chat Application - Monolithic Docker Image

FROM python:3.9-slim

WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Create directories
RUN mkdir -p static/uploads instance

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
