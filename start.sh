#!/bin/sh
ROLE=${ROLE:-worker}
if [ "$ROLE" = "manager" ]; then
    if [ ! -f /app/data/boilest.db ]; then
        cp /boil_hold/boilest.db /app/data/
    fi
    python -m scripts.check_rabbitmq_queues
    python start.py
    celery -A tasks worker -Q manager_queue
else
    python -m scripts.check_rabbitmq_queues
    celery -A tasks worker -Q worker_queue
fi