from datetime import datetime
import os, json, requests

def task_start_time(task):
    function_task_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ' + task + ' starting at ' + str(function_task_start_time) + '<<<<<<<<<<<<<<<<<<<')
    return function_task_start_time

def task_duration_time(task,function_task_start_time):
    function_task_duration_time = (datetime.now() - function_task_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ' + task + ' complete, executed for ' + str(function_task_duration_time) + ' minutes <<<<<<<<<<<<<<<<<<<')

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

def find_files(directory,extensions):
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith(extensions):
                # append the desired fields to the original json
                file = os.path.join(root,file)
                yield (file)