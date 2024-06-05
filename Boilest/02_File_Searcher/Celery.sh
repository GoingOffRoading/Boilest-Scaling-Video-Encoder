#!/bin/sh

echo "Getting this party started"

celery -A tasks worker -B -l INFO -Q manager -n manager@%n &
celery --broker=amqp://celery:celery@192.168.1.110:31672/celery flower
