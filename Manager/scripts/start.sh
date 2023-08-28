#!/bin/bash

celery -A tasks worker -l INFO  
#celery -A tasks flower --loglevel=INFO
