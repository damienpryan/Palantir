# homelab/palproj/Makefile
.PHONY: up down logs restart status build

up:
	@echo "Starting Palantir application services..."
	docker compose up --build -d

down:
	@echo "Stopping Palantir application services..."
	docker compose down -v

logs:
	@echo "Tailing Palantir application logs..."
	docker compose logs -f

restart: down up

status:
	@echo "Checking status of Palantir application services..."
	docker compose ps

build:
	@echo "Building Palantir application service images..."
	docker compose build

# --- Testing Targets ---
test:
    @echo "Running UNIT tests for palproj services (app, ingestion)..."
    # Example for 'app' service assuming pytest is used and tests are in /app/tests
    # docker compose run --rm app pytest /app/tests
    # Example for 'ingestion' service assuming pytest is used and tests are in /ingestion/tests
    # docker compose run --rm ingestion pytest /ingestion/tests
    @echo "No dedicated unit tests configured for palproj yet. Please set up tests/ directories and pytest calls."

test-integration:
    @echo "Running INTEGRATION tests for palproj services..."

    @echo "Checking app_db (PostgreSQL) readiness..."
    docker compose exec app_db pg_isready -U palantir_user -d palantir_app_db > /dev/null && echo "SUCCESS: app_db is ready." || (echo "FAILURE: app_db is NOT ready." && exit 1)

    @echo "Checking vector_db (PostgreSQL with pgvector) readiness..."
    docker compose exec vector_db pg_isready -U palantir_vector_user -d palantir_vector_db > /dev/null && echo "SUCCESS: vector_db is ready." || (echo "FAILURE: vector_db is NOT ready." && exit 1)

    @echo "Checking Flask app's /db_test endpoint (internal network)..."
    docker compose exec app curl --fail http://app:5000/db_test > /dev/null && echo "SUCCESS: Flask app /db_test endpoint is accessible." || (echo "FAILURE: Flask app /db_test endpoint is NOT accessible." && exit 1)

    @echo "Palproj integration tests passed."
