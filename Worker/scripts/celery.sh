#!/bin/sh -ex

echo "Checking Variables"
echo $Manager
echo $Worker

if [ $Manager == "Yes" ]; then
    echo "Running Manager and Worker" 
    celery -A tasks worker -B -l info -c 1 -Q manager &
    celery -A tasks flower -l debug 
else
    celery -A tasks worker -B -l info -c 1 -Q worker 
fi
