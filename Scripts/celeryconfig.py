import logging
from shared_services import celery_url_path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
print("Celery configuration loaded!")

broker_url = celery_url_path('amqp://')
result_backend = celery_url_path('rpc://')

from kombu import Exchange, Queue

# Define exchanges
manager_exchange = Exchange('manager_exchange', type='direct')
worker_exchange = Exchange('worker_exchange', type='direct')

# Define queues
task_queues = (
    Queue('manager', manager_exchange, routing_key='manager_routing_key', queue_arguments={'x-max-priority': 10}),
    Queue('worker', worker_exchange, routing_key='worker_routing_key', queue_arguments={'x-max-priority': 10}),
)

# Default queue settings
task_default_queue = 'worker'
task_default_exchange = 'worker_exchange'
task_default_routing_key = 'worker_routing_key'
task_default_priority = 5

# Concurrency and task settings
worker_concurrency = 1
task_acks_late = True
worker_prefetch_multiplier = 1

# Enable task events
worker_send_task_events = True
task_send_sent_event = True
task_track_started = True
worker_pool_restarts = True

# Update task routes
#task_routes = {
#    'queue_workers_if_queue_empty': {'queue': 'Manager'},
#    'locate_files': {'queue': 'Worker'},
#    'requires_encoding': {'queue': 'Worker'}
#}