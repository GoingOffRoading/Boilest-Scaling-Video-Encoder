#!/bin/sh -ex

echo "Checking Variables"
echo $Manager

if [ $Manager == "Yes" ]; then
    echo "Running Manager" 
    celery -A tasks worker -B -l info -c 1 -Q manager -n manager@%n &
    celery -A tasks flower -l debug 
else
    echo "Running Worker" 
    celery -A tasks worker -B -l info -c 1 -Q worker -n worker@%n
fi
