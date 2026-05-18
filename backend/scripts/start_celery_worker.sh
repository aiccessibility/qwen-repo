#!/bin/bash

# Celery Worker Startup Script for Accessibility Platform
# This script starts the Celery worker that processes audit tasks

set -e

echo "🚀 Starting Celery Worker..."
echo "📍 Working directory: $(pwd)"
echo "🔗 Redis URL: ${REDIS_URL:-redis://redis:6379/0}"

# Wait for Redis to be available using Python (more reliable than nc in minimal containers)
echo "⏳ Waiting for Redis to be ready..."
python3 -c "
import redis
import time
import os

redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
max_retries = 30
retry_delay = 1

for i in range(max_retries):
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print('✅ Redis is ready!')
        exit(0)
    except Exception as e:
        if i < max_retries - 1:
            time.sleep(retry_delay)
        else:
            print(f'❌ Redis not available after {max_retries} retries')
            exit(1)
"

# Start Celery worker with concurrency settings optimized for I/O bound tasks
exec celery -A app.celery_config.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=gevent \
    --prefetch-multiplier=1 \
    --hostname=accessibility_worker@%h \
    --queues=celery \
    --time-limit=3600 \
    --soft-time-limit=3300
