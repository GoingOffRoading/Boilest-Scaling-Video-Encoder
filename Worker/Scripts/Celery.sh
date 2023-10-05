#!/bin/sh -ex

echo "Checking Variables"
echo $Manager

if [ $Manager == "Yes" ]; then
    echo "Running Manager" 
    celery -A tasks worker -B -l WARNING -c 1 -Q manager,prober -n manager@%n &
    celery -A tasks flower -l WARNING 

elif [ $Manager == "Yes"] -a [ $Worker == "Yes"]; then
    echo "Running Worker & Manager" 
    celery -A tasks worker -B -l WARNING -c 1 -Q manager,worker,prober -n manager@%n &
    celery -A tasks flower -l WARNING 
else
    echo "Running Worker" 
    celery -A tasks worker -B -l WARNING info -c 1 -Q worker,prober -n worker@%n
fi
