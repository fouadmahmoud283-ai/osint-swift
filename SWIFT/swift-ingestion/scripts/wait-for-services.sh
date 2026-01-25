#!/bin/bash

# Wait for services to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -U swift; do
  sleep 1
done

echo "Waiting for Redis..."
while ! redis-cli -h redis ping; do
  sleep 1
done

echo "Waiting for MinIO..."
while ! curl -f http://minio:9000/minio/health/live; do
  sleep 1
done

echo "All services are ready!"

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

echo "Setup complete!"
