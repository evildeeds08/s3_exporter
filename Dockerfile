# Use the official Python image
FROM python:3.9-slim

# Install Rclone
RUN apt-get update && apt-get install -y rclone

# Install Python dependencies
RUN pip install prometheus_client

# Copy the Python script into the container
COPY s3_exporter.py /app/s3_exporter.py

# Copy the Rclone configuration file into the container
COPY rclone.conf /root/.config/rclone/rclone.conf

# Set the working directory
WORKDIR /app

# Define the command to run the Python script when the container starts
CMD ["python", "s3_exporter.py"]

