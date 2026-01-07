import pika
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_operation_queue():
    """Create the 'writes' queue for database_operation tasks"""
    # Get environment variables
    user = os.environ.get('user', 'celery')
    password = os.environ.get('password', 'celery')
    amqp_host = os.environ.get('celery_host', '192.168.1.110')
    amqp_port = int(os.environ.get('celery_port', '31672'))
    vhost = os.environ.get('celery_vhost', 'celery')

    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(
        host=amqp_host,
        port=amqp_port,
        virtual_host=vhost,
        credentials=credentials
    )

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare the 'writes' queue for database operations
        channel.queue_declare(
            queue='writes',
            durable=True,
            arguments={'x-max-priority': 10}
        )
        logger.info("Successfully created 'writes' queue for database_operation task")

        connection.close()
        return True

    except Exception as e:
        logger.error(f"Failed to create database_operation queue: {e}")
        raise

if __name__ == "__main__":
    create_database_operation_queue()
