# Use official Python image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy and Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#  Copy application code
COPY app/ ./app/        # Backend
COPY static/ ./static/  # Frontend

# Expose port (matches the one used in app.main)
EXPOSE 8080

# Start the FastAPI server with Uvicorn, binding to all interfaces and using port 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
