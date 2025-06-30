# Gemini Project Constitution for Palantir Homelab

This document is my primary reference for the Palantir project. I will consult this file at the beginning of each session to understand the architecture, key commands, and testing procedures.

## 1. High-Level Architecture

The project consists of two main Docker Compose stacks that communicate over a shared network.

-   **`gateway` Stack:**
    -   `nginx`: Acts as a reverse proxy and serves the static frontend files.
    -   `cloudflare-tunnel`: Securely exposes the `nginx` service to the internet.
-   **`palproj` Stack:**
    -   `app`: The core Flask/Python web application that handles business logic and API requests.
    -   `ingestion`: A Python script for processing and embedding code into the vector database.
    -   `app_db`: A PostgreSQL database for application data (e.g., chat history).
    -   `vector_db`: A PostgreSQL database with the `pgvector` extension for storing code embeddings.
-   **Networking:**
    -   Both stacks are connected via a shared external Docker network named `homelab_network`.
    -   The standard request flow is: `Browser -> Cloudflare -> cloudflare-tunnel -> nginx -> app`.
    -   Nginx proxies all requests starting with `/api/` to the `app` service at `http://app:5000/`.

## 2. Key Commands

All commands should be run from the root `/home/damien/Palantir` directory unless specified otherwise.

-   **Start/Restart Entire Application:** `make restart`
-   **Stop Entire Application:** `make down`
-   **View Logs for a Specific Stack:** `make logs stack=<stack_name>` (e.g., `make logs stack=palproj`)

## 3. The "Golden Path" Testing Strategy

After making any change, I will follow this testing sequence to ensure the system is healthy.

1.  **Test the Backend:** Run `make -C palproj test-integration`. This verifies that the Flask app, databases, and core logic are working correctly.
2.  **Test the Full Request Path:** Run `make -C gateway test_browser_simulation`. This simulates a request from a browser, testing the Nginx proxy, the network connection to the `app` service, and the final response.

## 4. Known Gotchas & Troubleshooting

-   **PRIMARY ISSUE: Browser Caching:** The browser can aggressively cache the frontend files (`app.js`, `index.html`). If the application misbehaves unexpectedly after a change, the **first step is always to perform a hard refresh (Ctrl+Shift+R) in the browser.**
-   **`404 Not Found` Errors:** If an API call fails with a 404, it means there is a mismatch between the URL in the frontend JavaScript (`gateway/nginx/html/app.js`) and the `location` block in the Nginx configuration (`gateway/nginx/nginx.conf`). They must both use the same path (e.g., `/api/`).
-   **`502 Bad Gateway` Errors:** This indicates the `nginx` service is not running or is unhealthy. Check its status with `make -C gateway status` and its logs with `make -C gateway logs`.

I will now adhere to this constitution for all future work on this project.