#!/bin/sh
echo "starting"
echo "Getting this party started"
python /Scripts/container_start.py

echo "Starting Flask"

# Set the Flask app file
FLASK_APP=Flask.py

# Set the Flask environment
export FLASK_ENV=development

# Set the host and port for the development server
#export FLASK_RUN_HOST=0.0.0.0
#export FLASK_RUN_PORT=5000

# Run the Flask app
flask run

echo "Flask Started"

echo "Starting Celery"
echo "Checking Variables"
echo "Manager is set to:" $Manager


if [ $Manager = "Yes" ]; then
    echo "Running Manager" 
    celery -A tasks_manager worker -B -l INFO -Q manager -n manager@%n &
    celery --broker=amqp://celery:celery@192.168.1.110:31672/celery flower
elif [ $Manager = "No" ]; then
    echo "Running Worker" 
    celery -A tasks_worker worker -l INFO -Q worker -n worker@%n
else
    echo "Everything is fucked"
fi
