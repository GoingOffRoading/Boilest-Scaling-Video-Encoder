from celery import Celery
from datetime import datetime
import json, os, requests
from task_shared_services import task_start_time, task_duration_time


app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

#@app.on_after_configure.connect
# Celery's scheduler.  Kicks off ffconfigs every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
#def setup_periodic_tasks(sender, **kwargs):
    # Calls ffconfigs('hello') every 10 seconds.
#    sender.add_periodic_task(86400.0, ffstarthere.s('hit it'))


# Function to check queue depth depending on queue name


def check_queue(queue_name):
    rabbitmq_host = os.environ['rabbitmq_host']
    rabbitmq_port = os.environ['rabbitmq_port']
    user = os.environ['user']
    password = os.environ['password']
    url = rabbitmq_host + ':' + str(rabbitmq_port) + '/api/queues/celery/' + queue_name
    print ('Checking RabbitMQ queue depth for: ' + queue_name)
    worker_queue = json.loads(requests.get(url, auth=(user,password)).text)
    queue_depth = (worker_queue["messages_unacknowledged"])
    return queue_depth

# Function to search for file, like media or configurations
def find_files(directory,extension):
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith(extension):
                # append the desired fields to the original json
                file = os.path.join(root,file)
                yield (file)

# Scan for condigurations, and post the to the next step
# Kicked off by the scheduler above, but started manually with start.py in /scripts
def find_configurations(arg):
    configurations = '/Boilest/Configurations' 
    extension = '.json'
    for i in find_files(configurations,extension):
        print (i)
        f = open(i)
        json_configuration = json.load(f)
        if json_configuration["enabled"] == 'true':
            print (json.dumps(json_configuration, indent=3, sort_keys=True))
            print ('sending ' + json_configuration["config_name"] + ' to ffinder')
            return(json_configuration)
        elif json_configuration["enabled"] == 'false':
            print ('Not condsidering ' + json_configuration["config_name"] + ' at this time') 
        else:
            print ('Something Broke')

def find_media(json_configuration):
    directory = (json_configuration['watch_folder'])
    extension = ('.mp4','.mkv','.avi')
    for i in find_files(directory,extension):
        print (i)


    



@app.task(queue='manager')
def ffstarthere(arg):
    task_start_time('ffstarthere')
    queue_depth = check_queue('worker')
    if queue_depth == 0:
        print ('queue depth is: ' + str(queue_depth) + ', kicking off the thing')
        for i in find_media:
            if encode_decision == 'yes':
                print ('Sending ' + file + ' to be encoded')
                ffinder.delay(json)
            elif encode_decision == 'no':
                print ('No need to encode ' + file +)
            else:
                print ('Something went wrong')
    elif queue_depth != 0:
        print ('Tasks in queue: ' + str(queue_depth) + ', not starting additional tasks')
    else:
        print ('Tasks in queue returned with an error')
    




