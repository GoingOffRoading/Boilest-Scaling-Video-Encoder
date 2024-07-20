import logging, os
from kombu import Exchange, Queue

# Configure logging
logging.basicConfig(level=logging.DEBUG)
print("Celery configuration loaded!")

def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    user = os.environ.get('user', 'celery')
    password = os.environ.get('password', 'celery')
    celery_host = os.environ.get('celery_host', '192.168.1.110')
    celery_port = os.environ.get('celery_port', '31672')
    celery_vhost = os.environ.get('celery_vhost', 'celery')
    thing = thing + user + ':' + password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
    logging.debug('celery_url_path is: ' + thing)
    return thing

broker_url = celery_url_path('amqp://')
result_backend = celery_url_path('rpc://')


# Define exchanges
worker_exchange = Exchange('worker_exchange', type='direct')


# Define queues
task_queues = (
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