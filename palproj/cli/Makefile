# Makefile for the CLI

.PHONY: all run test clean

# Build the Docker image
all: build

build:
	docker compose build cli

# Run the CLI using Docker Compose. Pass arguments using ARGS.
# Example: make run ARGS="chat 'hello world'"
run:
	docker compose run --rm cli $(ARGS)

# Run unit tests inside the container
test:
	docker compose run --rm cli python -m unittest discover -s tests

# Clean up dangling images
clean:
	docker image prune -f --filter "dangling=true"
