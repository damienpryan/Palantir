# homelab/gateway/Makefile

# This line tells 'make' that our targets don't correspond to actual files.
# It's a best practice to prevent conflicts and ensure commands always run.
.PHONY: up down logs restart status build test test-integration # <-- ADDED TEST TARGETS

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
	docker compose exec nginx curl --fail http://nginx:80 > /dev/null && echo "SUCCESS: Nginx is accessible." || (echo "FAILURE: Nginx is NOT accessible." && exit 1)

test-integration:
	@echo "Running INTEGRATION tests for gateway..."
	@echo "Checking Nginx static file service..."
	docker compose exec nginx curl --fail http://nginx:80 > /dev/null && echo "SUCCESS: Nginx is accessible." || (echo "FAILURE: Nginx is NOT accessible." && exit 1)
	@echo "Checking Flask app service..."
	docker compose exec nginx curl --fail http://app:5000

test-proxy:
	@echo "--- Testing Nginx to Flask App Proxy ---"
	docker compose exec nginx curl --fail http://app:5000/chat/test-from-proxy

test_browser_simulation:
	@echo "--- Simulating a browser request to the Nginx proxy ---"
	docker compose exec nginx curl --fail http://nginx/api/chat/hello%20world

