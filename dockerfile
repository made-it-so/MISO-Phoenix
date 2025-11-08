# Use a lightweight and secure Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY miso_main.py .

# Expose the port the container will listen on
# This MUST match your Gunicorn command and your Fargate Task/Service definition
EXPOSE 5000

# Set a non-root user for security
RUN useradd --no-log-init -u 1001 appuser
USER appuser

# Command to run the app using a production WSGI server (Gunicorn)
# This binds to all interfaces (0.0.0.0) on port 5000.
# We add --timeout 120 just in case, though this script should be instant.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "miso_main:app"]
