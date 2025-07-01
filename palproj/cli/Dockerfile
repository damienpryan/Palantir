# palproj/cli/Dockerfile

# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the CLI application code
COPY main.py .

# The entrypoint is the command that will be run when the container starts.
# We'll use this to execute our CLI script.
ENTRYPOINT ["python", "main.py"]

# The default command can be overridden when running the container.
CMD ["--help"]
