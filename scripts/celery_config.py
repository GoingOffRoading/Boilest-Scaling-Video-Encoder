import os

TASK_QUEUES = {
    'worker_queue': {
        'exchange': 'tasks',
        'exchange_type': 'direct',
        'routing_key': 'worker_queue',
        'queue_arguments': {'x-max-priority': 10},
    },
    'manager_queue': {
        'exchange': 'tasks',
        'exchange_type': 'direct',
        'routing_key': 'manager_queue',
        'queue_arguments': {'x-max-priority': 10},
    }
}

TASK_ROUTES = {
    'locate_files': {'queue': 'manager_queue'},
    'requires_encoding': {'queue': 'worker_queue'},
    'process_ffmpeg': {'queue': 'worker_queue'}
}

def configure_celery(app):
    app.conf.task_default_queue = 'worker_queue'
    app.conf.worker_concurrency = 1
    app.conf.worker_prefetch_multiplier = 1

    app.conf.task_queues = TASK_QUEUES
    app.conf.task_routes = TASK_ROUTES