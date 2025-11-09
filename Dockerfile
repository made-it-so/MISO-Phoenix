# Use a secure, slim base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# --- THIS IS THE FIX ---
# Install the 'git' binary into the container's OS
# We update apt, install git, then clean up to keep the image small
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# --- END OF FIX ---

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY miso_main.py .

# Expose the port Gunicorn will run on
EXPOSE 5000

# Add a non-root user for security
RUN useradd --no-log-init -u 1001 appuser
USER appuser

# Run the production server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "miso_main:app"]
