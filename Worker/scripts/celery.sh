#!/bin/sh -ex

echo "Checking Variables"
echo $Manager
echo $Worker

if [ $Manager == "Yes" -a $Worker == "Yes" ]; then
    echo "Running Manager and Worker" 
    celery -A tasks worker -B -l info -c 1 -Q worker,manager &
    celery -A tasks flower -l debug 
elif [ $Mmanager == "Yes" -a $Worker == "No" ]; then
    echo "Running Manager" 
    celery -A tasks worker -B -l info -c 1 -Q manager &
    celery -A tasks flower -l debug 
elif [ $Manager == "No" -a $Worker == "Yes" ]; then
    echo "Running Worker" 
    celery -A tasks worker -B -l info -c 1 -Q worker 
else
    echo "We have a problem"
fi
