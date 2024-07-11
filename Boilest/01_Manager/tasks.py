from celery import Celery
import logging, os, requests
import celeryconfig
from shared_services import celery_url_path
#from worker.tasks import locate_files


app = Celery('manager', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

app.autodiscover_tasks(['manager.tasks'])

@app.task(queue='manager')
def queue_workers_if_queue_empty(arg):
    try:
        manager_queue_depth = check_queue('manager') + get_active_tasks('manager')
        worker_queue_depth = check_queue('worker') + get_active_tasks('worker')
        queue_depth = worker_queue_depth + manager_queue_depth
        
        logging.info(f'Current Worker queue depth is: {queue_depth}')
        print(f'Current Worker queue depth is: {queue_depth}')
        
        if queue_depth == 0:
            logging.debug('Starting locate_files')
            app.send_task('worker.app.locate_files', kwarg = {'arg':arg}, priority=1) 
        elif queue_depth > 0:
            logging.debug(f'{queue_depth} tasks in queue. No rescan needed at this time.')
        else:
            logging.error('Something went wrong checking the Worker Queue')
    
    except Exception as e:
        logging.error(f"Error in queue_workers_if_queue_empty: {e}")


@app.on_after_configure.connect
# Celery's scheduler.  Kicks off queue_workers_if_queue_empty every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(3600.0, queue_workers_if_queue_empty.s('hit it'), name='queue_workers_every_hour')


def get_active_tasks(queue_name)-> int:
    try:
        with app.connection() as connection:
            celery_control = app.control
            active_tasks = celery_control.inspect().active(queue_name)

            if active_tasks is not None and queue_name in active_tasks:
                task_count = len(active_tasks[queue_name])
                logging.debug(f'get_active_tasks tasks in-progress for {queue_name} is: {task_count}')
                return task_count
            else:
                # No active tasks in the specified queue
                logging.debug ('Remaining tasks in progress: 0')
                return 0
    except Exception as e:
        logging.error(f"Error getting active tasks count: {e}")
        return -1 # Return -1 to indicate an error


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
