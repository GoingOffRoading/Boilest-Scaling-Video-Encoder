#!/bin/sh -ex

echo "Checking Variables"
echo $Manager

if [ $Manager == "Yes" ]; then
    echo "Running Manager" 
    celery -A tasks worker -B -l WARNING -c 1 -Q manager -n manager@%n &
    celery -A tasks flower -l WARNING 

elif [ $Manager == "Yes"] -a [ $Worker == "Yes"]; then
    echo "Running Worker & Manager" 
    celery -A tasks worker -B -l WARNING -c 1 -Q manager,worker -n manager@%n &
    celery -A tasks flower -l WARNING 
else
    echo "Running Worker" 
    celery -A tasks worker -B -l WARNING info -c 1 -Q worker -n worker@%n
fi
