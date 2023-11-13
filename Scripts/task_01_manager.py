from celery import Celery
from datetime import datetime
import json, os, requests
from task_02_prober import fprober

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

#@app.on_after_configure.connect
# Celery's scheduler.  Kicks off ffconfigs every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
#def setup_periodic_tasks(sender, **kwargs):
    # Calls ffconfigs('hello') every 10 seconds.
#    sender.add_periodic_task(86400.0, ffconfigs.s('hit it'))


def task_start_time(task):
    function_task_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ' + task + ' starting at ' + str(function_task_start_time) + '<<<<<<<<<<<<<<<<<<<')
    return function_task_start_time

def task_duration_time(task,function_task_start_time):
    function_task_duration_time = (datetime.now() - function_task_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ' + task + ' complete, executed for ' + str(function_task_duration_time) + ' minutes <<<<<<<<<<<<<<<<<<<')

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

# Function to search for the json configurations
def find_files(directory,extension):
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith(extension):
                # append the desired fields to the original json
                json_file = os.path.join(root,file)
                yield (json_file)

@app.task(queue='manager')
# Scan for condigurations, and post the to the next step
# Kicked off by the scheduler above, but started manually with start.py in /scripts
def ffconfigs(arg):
    function_task_start_time = task_start_time('ffconfigs')
    print ('Arg is: ' + arg)

    configurations = '/Boilest/Configurations'
    
    # Searching for configurations
    if check_queue('worker') == 0:
        print ('queue depth is 0')
        for i in find_files(configurations,'.json'):
            print (i)
            f = open(i)
            json_template = json.load(f)
            if json_template["enabled"] == 'true':
                print (json.dumps(json_template, indent=3, sort_keys=True))
                print ('sending ' + json_template["config_name"] + ' to ffinder')
                ffinder.delay(json_template)
            elif json_template["enabled"] == 'false':
                print ('Not condsidering ' + json_template["config_name"] + ' at this time') 
            else:
                print ('Something Broke')
    elif check_queue('worker') != 0:
        print ('Tasks in queue: ' + str(queue_depth) + ', not starting additional tasks')
    else:
        print ('Tasks in queue returned with an error')

    task_duration_time('ffconfigs',function_task_start_time)


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

