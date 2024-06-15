# celeryconfig.py
import logging, os
print("Celery configuration loaded!")

def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    user = os.environ.get('user','celery') 
    password = os.environ.get('password','celery')
    celery_host = os.environ.get('celery_host','192.168.1.110')
    celery_port = os.environ.get('celery_port', '31672')
    celery_vhost = os.environ.get('celery_vhost','celery')
    thing = thing + user + ':' + password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
    logging.debug ('celery_url_path is: ' + thing)
    return thing

broker_url = celery_url_path('amqp://')
result_backend = celery_url_path('rpc://')

# Define two queues with x-max-priority
task_queues = {
    'manager': {
        'exchange': 'manager_exchange',
        'exchange_type': 'direct',
        'routing_key': 'manager_routing_key',
        'queue_arguments': {'x-max-priority': 10},
        'default_priority': 5 # Set the default priority for tasks in this queue
    },
    'file_searcher': {
        'exchange': 'file_searcher_exchange',
        'exchange_type': 'direct',
        'routing_key': 'file_searcher_routing_key',
        'queue_arguments': {'x-max-priority': 10},
        'default_priority': 5 # Set the default priority for tasks in this queue
    }, 
    'worker': {
        'exchange': 'worker_exchange',
        'exchange_type': 'direct',
        'routing_key': 'worker_routing_key',
        'queue_arguments': {'x-max-priority': 10},
        'default_priority': 5 # Set the default priority for tasks in this queue
    }, 
    
}

# Set concurrency to 1
worker_concurrency = 1
task_acks_late = True

# Set prefetch_count to 1
worker_prefetch_multiplier = 1

# Enable task events
worker_send_task_events = True
task_send_sent_event = True
task_track_started = True
worker_pool_restarts = True