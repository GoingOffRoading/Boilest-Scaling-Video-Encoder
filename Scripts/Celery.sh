#!/bin/sh
echo "starting"
echo "Getting this party started"
python container_start.py

echo "Checking to see if Boilest DB Exists"
python ./DB/create_boilest_db.py

echo "Checking Variables"
echo "Manager is set to:" $Manager
echo "Worker is set to:" $Worker
echo "Starting Celery"

if [ $Manager = "Yes" -a $Worker = "No" ]; then
    echo "Running Manager" 
    celery -A tasks worker -B -l WARNING  -c 1 -Q manager -n manager@%n -S /Boilest/worker.state -f /Boilest/Logs/celery.logs &
    celery -A tasks flower -l INFO
elif [ $Manager = "No" -a $Worker = "Yes" ]; then
    echo "Running Worker" 
    celery -A tasks worker -B -l WARNING  -c 1 -Q worker -n encoder@%n 
elif [ $Manager = "Yes" -a $Worker = "Yes" ]; then
    echo "Running Manager & Worker" 
    celery -A tasks worker -B -l WARNING  -c 1 -Q manager -n manager@%n -S /Boilest/worker.state -f /Boilest/Logs/celery.logs &
    celery -A tasks flower -l WARNING 
    celery -A tasks worker -B -l WARNING  -c 1 -Q worker -n encoder@%n 
else
    echo "Everything is fucked"
fi
