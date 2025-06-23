# Use a slim Python base image for smaller size
FROM python:3.10-slim-bookworm

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port your Flask app will run on
EXPOSE 5000

# Command to run the Flask application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "main:app"]
