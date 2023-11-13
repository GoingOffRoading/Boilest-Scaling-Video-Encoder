#!/bin/sh
echo "starting"
echo "Getting this party started"
python container_start.py

echo "Checking to see if Boilest DB Exists"
python ./DB/create_boilest_db.py

echo "Checking Variables"
echo "Manager is set to:" $Manager
echo "Starting Celery"

if [ $Manager = "Yes" ]; then
    echo "Running Manager" 
    celery -A task_01_manager worker -B -l INFO -c 1 -Q manager -n manager@%n -S /Boilest/worker.state &
    celery -A task_01_manager flower -l INFO
elif [ $Manager = "No" ]; then
    echo "Running Worker" 
    celery -A task_03_fencoder worker -l INFO -c 1 -Q worker -n worker@%n 
else
    echo "Everything is fucked"
fi
