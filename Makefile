# homelab/Makefile - Master Orchestrator

# Add the new dump targets to the .PHONY list
.PHONY: up down logs restart status dump-all dump-gateway dump-palproj

# --- Service Management Targets ---
up:
	@echo "--- Starting all homelab stacks (gateway -> palproj) ---"
	$(MAKE) -C gateway up
	$(MAKE) -C palproj up

down:
	@echo "--- Stopping all homelab stacks (palproj -> gateway) ---"
	$(MAKE) -C palproj down
	$(MAKE) -C gateway down

logs:
	@if [ -z "$(stack)" ]; then \
	    echo "--- Tailing combined logs for all stacks ---"; \
	    docker compose -f gateway/docker-compose.yml -f palproj/docker-compose.yml logs -f; \
	else \
	    echo "--- Tailing logs for $(stack) stack ---"; \
	    $(MAKE) -C $(stack) logs; \
	fi

restart: down up

status:
	@echo "--- Status for gateway stack ---"
	$(MAKE) -C gateway status
	@echo "\n--- Status for palproj stack ---"
	$(MAKE) -C palproj status

# --- AI Context Dumping Targets ---
# Dumps the entire project from the homelab root.
dump-all:
	@echo "Dumping all project files to homelab_dump.txt..."
	./dump_project.sh > homelab_dump.txt

# Dumps only the gateway subdirectory.
dump-gateway:
	@echo "Dumping gateway files to gateway_dump.txt..."
	(cd gateway && ../dump_project.sh) > gateway_dump.txt

# Dumps only the palproj subdirectory.
dump-palproj:
	@echo "Dumping palproj files to palproj_dump.txt..."
	(cd palproj && ../dump_project.sh) > palproj_dump.txt
