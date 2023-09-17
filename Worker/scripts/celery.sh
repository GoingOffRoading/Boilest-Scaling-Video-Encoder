#!/bin/sh -ex

celery -A tasks worker -B -l info -c 1 &
celery -A tasks flower -l debug 

# --detach