# Use a lightweight Python base image
FROM python:3.10-slim-bookworm

# Set the working directory
WORKDIR /ingestion

# Copy requirements.txt and install dependencies FIRST for better Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory into the container (which will be empty for now)
COPY . .

# We won't define a CMD yet, as ingestion will be run manually or via a cron job
# CMD ["python", "ingestion_script.py"]
