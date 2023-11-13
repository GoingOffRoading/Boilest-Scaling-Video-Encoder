from celery import Celery
from datetime import datetime
import json, os, requests
from task_03_ffinder import ffinder

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')


# We're going to break up the workflow based on the nature of the task
# I.E. vido, audio, subtitle, etc

# What we probably want here is:
# A seperate function that checks the queue given a queue name
# a seperate function that checks the directory related to the function

@app.task(queue='manager')

rabbitmq_host = os.environ['rabbitmq_host']
rabbitmq_port = os.environ['rabbitmq_port']
user = os.environ['user']
password = os.environ['password']

configurations = '/Boilest/Configurations'

# Function to check queue depth depending on queue name
def check_queue(queue_name):
    url = rabbitmq_host + ':' + str(rabbitmq_port) + '/api/queues/celery/' + queue_name
    print ('Checking RabbitMQ queue depth for: ' + queue_name)
    worker_queue = json.loads(requests.get(url, auth=(user,password)).text)
    queue_depth = (worker_queue["messages_unacknowledged"])
    return queue_depth

# Function to search for the json configurations
def find_configurations(directory):
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.json'):
                # append the desired fields to the original json
                json_file = os.path.join(root,file)
                yield (json_file)

# Scan for condigurations, and post the to the next step
# Kicked off by the scheduler above, but started manually with start.py in /scripts
def ffconfigs(arg):
    ffconfig_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffconfigs with the arg: ' + arg + ' starting at ' + str(ffconfig_start_time) + '<<<<<<<<<<<<<<<<<<<')
     
    queue_depth = check_queue('worker')
    # Searching for configurations
    if queue_depth == 0:
        for i in find_configurations(configurations):
            print (i)
            f = open(i)
            json_template = json.load(f)
            print (json.dumps(json_template, indent=3, sort_keys=True))
            print ('sending ' + json_template["config_name"] + ' to ffinder')
            ffinder.delay(json_template)
    elif queue_depth != 0:
        print ('Tasks in queue: ' + str(queue_depth) + ', not starting config scan')
    else:
        print ('Tasks in queue returned with an error')


    ffconfig_duration = (datetime.now() - ffconfig_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffconfigs ' + arg + ' complete, executed for ' + str(ffconfig_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

