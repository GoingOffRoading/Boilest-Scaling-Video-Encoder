# celeryconfig.py

from task_shared_services import celery_url_path

print("Celery configuration loaded!")

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