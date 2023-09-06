from celery import Celery
import os
import subprocess
import shlex
import json
import time
from pathlib import Path

app = Celery('tasks', backend = 'rpc://test:test@192.168.1.110:31672/celery', broker = 'amqp://test:test@192.168.1.110:31672/celery')

@app.task
json_file = f'C:\\Users\\Chase\\media\\Newfolder\\AV1.json'
mygenerator = finder(json_file) 
for finder_data in mygenerator:
    print(finder_data)
        

@app.task
def ffprober(FILEPATH):



@app.task
def ffencode(JOBJSON):









@app.task
def ffstatrecorde(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF):
    ffstatrecorder(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF)


