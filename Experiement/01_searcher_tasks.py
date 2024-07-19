from celery import Celery
import json, os, logging, requests
from shared_services import celery_url_path

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
# >>>>>>>>>>>>>>> Celery Configurations >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  


app = Celery('searcher_tasks', broker = celery_url_path('amqp://') )

app.conf.task_queues = {
    'searcher_queue': {
        'exchange': 'tasks',
        'exchange_type': 'direct',
        'routing_key': 'searcher_queue',
        'queue_arguments': {'x-max-priority': 10},
    }
}

app.conf.task_routes = {
    'searcher_tasks.locate_files': {'queue': 'searcher_queue'},
    'searcher_tasks.locate_files': {'queue': 'searcher_queue'},
}


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>> Check queue depth >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

@app.task
def queue_workers_if_queue_empty(arg):
    try:
        queue_depth = check_queue('Worker')        
        print(f'Current Worker queue depth is: {queue_depth}')
        print(f'Current Worker queue depth is: {queue_depth}')        
        if queue_depth == 0:
            print('Starting locate_files')
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            #locate_files.apply_async(kwargs={'arg': arg}, priority=1)
            locate_files.apply_async(('arg': arg), queue='searcher_queue', priority=5)
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
        elif queue_depth > 0:
            logging.debug(f'{queue_depth} tasks in queue. No rescan needed at this time.')
        else:
            logging.error('Something went wrong checking the Worker Queue')
    
    except Exception as e:
        logging.error(f"Error in queue_workers_if_queue_empty: {e}")


def check_queue(queue_name):
    try:
        rabbitmq_host = 'http://' + os.environ.get('rabbitmq_host','192.168.1.110')
        rabbitmq_port = os.environ.get('rabbitmq_port','32311')
        user = os.environ.get('user','celery')
        password = os.environ.get('password','celery')
        celery_vhost = os.environ.get('celery_vhost','celery')

        url = f"{rabbitmq_host}:{rabbitmq_port}/api/queues/{celery_vhost}/{queue_name}"
        logging.debug(f'Checking RabbitMQ queue depth for: {queue_name}')

        response = requests.get(url, auth=(user, password))
        response.raise_for_status()  # Ensure we raise an exception for HTTP errors

        worker_queue = response.json()
        queue_depth = worker_queue.get("messages_unacknowledged", 0)

        logging.debug (f'check_queue queue depth is: ' + str(queue_depth))
        return queue_depth
    except Exception as e:
        logging.error(f"Error getting active tasks count: {e}")
        return -1 # Return -1 to indicate an error


# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the files by searching directories
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

@app.task
def locate_files(arg):
    directories = ['/anime', '/tv', '/movies']
    extensions = ['.mp4', '.mkv', '.avi']

    print(f'Searching directories: {directories}')
    print(f'File extensions: {extensions}')

    for file_located in find_files(directories, extensions):
        logging.debug('File located, sending to ffprobe function')
        try:
            file_located_data = json.loads(file_located)
            logging.debug(json.dumps(file_located_data, indent=3, sort_keys=True))
            print(json.dumps(file_located_data, indent=3, sort_keys=True))
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            #requires_encoding.apply_async(kwargs={'file_located_data': file_located_data}, priority=2)
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
        except json.JSONDecodeError as e:
            logging.error(f'Failed to decode JSON: {e}')
            continue

def find_files(directories, extensions):
    for directory in directories:
        logging.info ('Scanning: ' + directory)
        for root, dirs, files in os.walk(directory):
            for file in files:
                for ext in extensions:
                    if file.lower().endswith(ext.lower()):
                        file_path = os.path.join(root, file)
                        result_dict = {
                            'directory': directory,
                            'root': root,
                            'file': file,
                            'file_path': file_path,
                            'extension': ext
                        }
                        yield json.dumps(result_dict)
