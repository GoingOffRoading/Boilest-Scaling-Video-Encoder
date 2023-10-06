#!/bin/sh

echo "Checking Variables"
echo "Manager is set to:" $Manager
echo "Worker is set to:" $Worker

if [ $Manager = "Yes" -a $Worker = "No" ]; then
    echo "Running Manager" 
    celery -A tasks worker -B -l WARNING -c 1 -Q manager,prober -n manager@%n &
    celery -A tasks flower -l WARNING 
elif [ $Manager = "Yes" -a $Worker = "Yes" ]; then
    echo "Running Worker & Manager" 
    celery -A tasks worker -B -l WARNING -c 1 -Q manager,worker,prober -n manager@%n &
    celery -A tasks flower -l WARNING 
elif [ $Manager = "No" -a $Worker = "Yes" ]; then
    echo "Running Worker" 
    celery -A tasks worker -B -l WARNING -c 1 -Q worker,prober -n worker@%n
else
    echo "Everything is fucked"
fi
