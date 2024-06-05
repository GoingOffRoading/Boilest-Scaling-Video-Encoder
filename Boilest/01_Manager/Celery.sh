#!/bin/sh
echo "starting"
echo "Getting this party started"
python /Scripts/container_start.py

echo "Starting Flask"
nohup flask run > log.txt 2>&1 &
echo "Flask Started"
echo "Running Manager" 
celery -A tasks_manager worker -B -l INFO -Q manager -n manager@%n &
celery --broker=amqp://celery:celery@192.168.1.110:31672/celery flower