from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib
from task_03_ffinder import ffinder

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')


# We're going to break up the workflow based on the nature of the task
# I.E. vido, audio, subtitle, etc

# What we probably want here is:
# A seperate function that checks the queue given a queue name
# a seperate function that checks the directory related to the function







@app.task(queue='manager')
# Scan for condigurations, and post the to the next step
# Kicked off by the scheduler above, but started manually with start.py in /scripts
def ffconfigs(arg):
    ffconfig_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffconfigs with the arg: ' + arg + ' starting at ' + str(ffconfig_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # First, we need to check the queue depth.  We don't want to add to queue, or add duplicate tasks, if there are already tasks in the queue 
    worker_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/worker', auth=('celery', 'celery'))).text)
    worker_queue_messages_unacknowledged = (worker_queue["messages_unacknowledged"])
    manager_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/manager', auth=('celery', 'celery'))).text)
    manager_queue_messages_unacknowledged = (manager_queue["messages_unacknowledged"])      
    tasks = worker_queue_messages_unacknowledged + manager_queue_messages_unacknowledged
    
    directory = '/Boilest/Configurations'
    # Searching for configurations
    if tasks == 0:
        print ('No tasks in sque, starting search for configs')
        for root, dirs, files in os.walk(directory):
            # select file name
            for file in files:
                # check the extension of files
                if file.endswith('.json'):
                    # append the desired fields to the original json
                    json_file = os.path.join(root,file)
                    print (json_file)
                    f = open(json_file)
                    json_template = json.load(f)
                    print (json.dumps(json_template, indent=3, sort_keys=True))
                    print ('sending ' + json_template["config_name"] + ' to ffinder')
                    ffinder.delay(json_template)
                else:
                    print('Did not find Configurations')
    elif tasks != 0:
        print ('Tasks in queue: ' + str(tasks) + ', not starting config scan')
    else:
        print ('Tasks in queue returned with an error')
    ffconfig_duration = (datetime.now() - ffconfig_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffconfigs ' + arg + ' complete, executed for ' + str(ffconfig_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

