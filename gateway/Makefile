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

# --- Testing Targets ---
test:
    @echo "Running UNIT tests for gateway service..."
    # Placeholder: Add actual frontend/Nginx config unit tests here if applicable.
    @echo "No dedicated unit tests configured for gateway yet. (Add npm/js tests here if applicable)"

test-integration:
    @echo "Running INTEGRATION tests for gateway..."
    @echo "Checking Nginx static file service (localhost:80)..."
    # curl --fail makes curl exit with an error code if the request fails (e.g., 4xx/5xx status)
    # > /dev/null suppresses output, && ... || (...) provides success/failure message
    curl --fail http://localhost:80 > /dev/null && echo "SUCCESS: Nginx on localhost:80 is accessible." || (echo "FAILURE: Nginx on localhost:80 is NOT accessible." && exit 1)

    @echo "Checking Nginx static file service (ryancs.com.au)..."
    curl --fail http://ryancs.com.au > /dev/null && echo "SUCCESS: Nginx on ryancs.com.au is accessible." || (echo "FAILURE: Nginx on ryancs.com.au is NOT accessible." && exit 1)

    @echo "Gateway integration tests passed."
