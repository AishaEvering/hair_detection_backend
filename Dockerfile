# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV FLASK_APP=wsgi:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the Flask application with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "wsgi:app"]
