import pika
import os
import logging
from scripts.celery_config import TASK_QUEUES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def declare_queues():
    # Get environment variables
    user = os.environ.get('user', 'celery')
    password = os.environ.get('password', 'celery')
    host = os.environ.get('rabbitmq_host', '192.168.1.110')
    port = int(os.environ.get('rabbitmq_port', '32311'))  # Assuming this is AMQP port, but wait, earlier it's 32311 for rabbitmq_port, but AMQP is 31672
    vhost = os.environ.get('celery_vhost', 'celery')

    # Wait, rabbitmq_port is 32311, but in ENV it's rabbitmq_port 32311, but AMQP is celery_port 31672
    # Probably rabbitmq_port is for management, but for pika, need AMQP port.
    # The ENV has celery_port 31672 for AMQP, rabbitmq_port 32311 perhaps management.
    # So, for pika, use celery_host and celery_port.

    amqp_host = os.environ.get('celery_host', '192.168.1.110')
    amqp_port = int(os.environ.get('celery_port', '31672'))

    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host=amqp_host, port=amqp_port, virtual_host=vhost, credentials=credentials)

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare queues using the same config as Celery
        for queue_name, queue_config in TASK_QUEUES.items():
            args = queue_config.get('queue_arguments', {})
            channel.queue_declare(queue=queue_name, durable=True, arguments=args)
            logger.info(f"Declared queue: {queue_name}")

        connection.close()
        logger.info("All queues declared successfully")

    except Exception as e:
        logger.error(f"Failed to declare queues: {e}")
        raise

if __name__ == "__main__":
    declare_queues()