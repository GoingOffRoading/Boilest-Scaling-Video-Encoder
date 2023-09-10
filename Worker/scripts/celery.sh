#!/bin/sh -ex

celery -A tasks worker -l info -c 1 &
celery -A tasks flower -l debug 

# --detach