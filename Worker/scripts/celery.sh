#!/bin/sh -ex

celery -A tasks worker -B -l info -c 1 -q manager, worker &
celery -A tasks flower -l debug 

# --detach