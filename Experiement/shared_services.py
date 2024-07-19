import os


def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    user = os.environ('celery_user', 'celery')
    password = os.environ('celery_password', 'celery')
    celery_host = os.environ('celery_host', '192.168.1.110')
    celery_port = os.environ('celery_port', '31672')
    celery_vhost = os.environ('celery_vhost', 'celery')
    thing = thing + user + ':' + password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
    print('celery_url_path is: ' + thing)
    return thing