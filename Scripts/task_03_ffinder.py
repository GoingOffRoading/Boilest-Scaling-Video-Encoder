from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib
from task_04_fprober import fprober

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

@app.task(queue='manager')
def ffinder(json_template):
    # The purpose of this function of to search a directory for files, filter for specific formats, and send those filtered results to the next function
    ffinder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffinder executing with config: ' + json_template["config_name"] + ' starting at ' + str(ffinder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # For fun/diagnostics
    print (json.dumps(json_template, indent=3, sort_keys=True))

    # Get the folder to scan
    directory = (json_template['watch_folder'])
    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')

    # traverse whole directory
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
                # append the desired fields to the original json
                ffinder_json = {'file_path':root, 'file_name':file}
                ffinder_json.update(json_template)      
                print(json.dumps(ffinder_json, indent=3, sort_keys=True))
                fprober.delay(ffinder_json)

    ffinder_duration = (datetime.now() - ffinder_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffinder config: ' + json_template["config_name"] + ' complete, executed for ' + str(ffinder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

