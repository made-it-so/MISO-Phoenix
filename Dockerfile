# Start from an official Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install git
RUN apt-get update && apt-get install -y git

# Install all Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now, copy all of our application code into the container
# (We will create a .dockerignore to skip venv)
COPY . .

# Expose port 5000 to the outside world
EXPOSE 5000

# This is the command that runs when the container starts
# It's the same command you've been running manually
CMD ["flask", "--app", "miso_main", "run", "--host=0.0.0.0", "--port=5000"]
