#!/bin/sh
set -e

# Wait for the app service to be available
while ! nc -z app 5000; do
  echo "Waiting for app service..."
  sleep 1
done

echo "App service is up - starting nginx"
nginx -g 'daemon off;'
