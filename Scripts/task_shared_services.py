from datetime import datetime
import os, json, requests, shutil

def task_start_time(task):
    function_task_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ' + task + ' starting at ' + str(function_task_start_time) + '<<<<<<<<<<<<<<<<<<<')
    return function_task_start_time

def task_duration_time(task,function_task_start_time):
    function_task_duration_time = (datetime.now() - function_task_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ' + task + ' complete, executed for ' + str(function_task_duration_time) + ' minutes <<<<<<<<<<<<<<<<<<<')

def check_queue(queue_name):
    rabbitmq_host = os.environ['rabbitmq_host']
    rabbitmq_port = os.environ['rabbitmq_port']
    user = os.environ['user']
    password = os.environ['password']
    url = rabbitmq_host + ':' + str(rabbitmq_port) + '/api/queues/celery/' + queue_name
    print ('Checking RabbitMQ queue depth for: ' + queue_name)
    worker_queue = json.loads(requests.get(url, auth=(user,password)).text)
    queue_depth = (worker_queue["messages_unacknowledged"])
    return queue_depth

def find_files(directory,extensions):
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith(extensions):
                # append the desired fields to the original json
                file = os.path.join(root,file)
                yield (file)

def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    thing = thing + os.environ['user'] + ':' + os.environ['password'] + '@' + os.environ['celery_host'] + ':' + os.environ['celery_port'] + '/' + os.environ['celery_vhost']
    return thing

def file_size_mb(file_path):
    # Used a bit in tasks_worker
    file_size = round(os.stat(file_path).st_size / (1024 * 1024))
    return file_size

def copy_directory_contents(source_directory, destination_directory):
    try:
        # Create the destination directory if it doesn't exist
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory)

        # Copy all contents of the source directory to the destination directory
        for item in os.listdir(source_directory):
            source_item = os.path.join(source_directory, item)
            destination_item = os.path.join(destination_directory, item)

            if os.path.isdir(source_item):
                # Recursively copy subdirectories
                shutil.copytree(source_item, destination_item)
            else:
                # Copy files
                shutil.copy2(source_item, destination_item)

        print("Contents copied successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def is_directory_empty_recursive(directory_path):
    # Check to see if a directory is empty, return True if Empty
    for root, dirs, files in os.walk(directory_path):
        # If there are any files or subdirectories, the directory is not empty
        if files or dirs:
            return False
    # If the loop completes without returning, the directory and its subdirectories are empty
    return True
