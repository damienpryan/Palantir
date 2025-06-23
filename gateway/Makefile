# homelab/gateway/Makefile

# This line tells 'make' that our targets don't correspond to actual files.
# It's a best practice to prevent conflicts and ensure commands always run.
.PHONY: up down logs restart status build

# Start all services in detached mode, building images if necessary.
up:
    @echo "Starting gateway services..."
    docker compose up --build -d

# Stop and remove all services, networks, and volumes.
down:
    @echo "Stopping gateway services and cleaning up..."
    docker compose down -v

# View the live logs for all running services.
logs:
    @echo "Tailing gateway logs (Press Ctrl+C to exit)..."
    docker compose logs -f

# Restart all services (run 'down' then 'up').
restart: down up

# Show the status of running containers.
status:
    @echo "Checking status of gateway services..."
    docker compose ps

# Force a rebuild of the service images.
build:
    @echo "Building gateway service images..."
    docker compose build
