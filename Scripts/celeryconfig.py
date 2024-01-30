# celeryconfig.py

from task_shared_services import celery_url_path

print("Celery configuration loaded!")

BROKER_URL = celery_url_path('amqp://')
CELERY_RESULT_BACKEND = celery_url_path('rpc://')

# Define two queues with x-max-priority
CELERY_QUEUES = {
    'manager': {
        'exchange': 'manager_exchange',
        'exchange_type': 'direct',
        'routing_key': 'manager_routing_key',
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
CELERYD_CONCURRENCY = 1

# Set prefetch_count to 1
CELERYD_PREFETCH_MULTIPLIER = 1

# Enable task events
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True
CELERY_TRACK_STARTED = True
CELERYD_POOL_RESTARTS = True