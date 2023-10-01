my_app = Celery(...)

# Inspect all nodes.
i = my_app.control.inspect()

# Show the items that have an ETA or are scheduled for later processing
i.scheduled()

# Show tasks that are currently active.
i.active()

# Show tasks that have been claimed by workers
i.reserved()



https://stackoverflow.com/questions/5544629/retrieve-list-of-tasks-in-a-queue-in-celery


https://docs.celeryq.dev/en/latest/userguide/workers.html#inspecting-workers

from celery.task.control import inspect
i = inspect()
i.reserved()


https://stackoverflow.com/questions/10889557/in-celery-how-to-get-task-position-in-queue

https://stackoverflow.com/questions/74571031/how-can-i-know-the-queues-created-in-celery-with-q-argument

https://stackoverflow.com/questions/58305650/celery-redis-backend-how-to-limit-queue-size

https://stackoverflow.com/questions/67676843/how-can-i-get-waitress-queuetask-depth-programmatically

https://stackoverflow.com/questions/18631669/django-celery-get-task-count