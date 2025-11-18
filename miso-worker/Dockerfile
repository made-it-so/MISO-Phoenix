# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables to ensure logs show up in CloudWatch
ENV PYTHONUNBUFFERED=1

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ .

# Run the worker
CMD ["python", "worker.py"]
