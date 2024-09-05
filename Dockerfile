# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV FLASK_APP=wsgi:app
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the Flask application with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "wsgi:app"]

LABEL maintainer="Aisha Evering"
LABEL version="1.0"
LABEL description="flask api for object detection"
