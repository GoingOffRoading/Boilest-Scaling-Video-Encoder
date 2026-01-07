import os

TASK_QUEUES = {
    'database_operation ': {
        'exchange': 'tasks',
        'exchange_type': 'direct',
        'routing_key': 'database_operation ',
        'queue_arguments': {'x-max-priority': 10},
    },
    'encode_queue ': {
        'exchange': 'tasks',
        'exchange_type': 'direct',
        'routing_key': 'encode_queue ',
        'queue_arguments': {'x-max-priority': 10},
    }
}

TASK_ROUTES = {
    'encode_queue': {'queue': 'encode_queue'},
    'database_operation': {'queue': 'database_operation'}
}

def configure_celery(app):
    app.conf.worker_concurrency = 1
    app.conf.worker_prefetch_multiplier = 1

    app.conf.task_queues = TASK_QUEUES
    app.conf.task_routes = TASK_ROUTES