from datetime import datetime
import os, json, requests, shutil, subprocess

def task_start_time(task):
    function_task_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ' + task + ' starting at ' + str(function_task_start_time) + '<<<<<<<<<<<<<<<<<<<')
    return function_task_start_time

def task_duration_time(task,function_task_start_time):
    function_task_duration_time = (datetime.now() - function_task_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ' + task + ' complete, executed for ' + str(function_task_duration_time) + ' minutes <<<<<<<<<<<<<<<<<<<')

def check_queue(queue_name):
    rabbitmq_host = 'http://' + os.environ.get('rabbitmq_host','192.168.1.110')
    rabbitmq_port = os.environ.get('rabbitmq_port','32311')
    user = os.environ.get('user','celery')
    password = os.environ.get('password','celery')
    url = rabbitmq_host + ':' + str(rabbitmq_port) + '/api/queues/celery/' + queue_name
    print ('Checking RabbitMQ queue depth for: ' + queue_name)
    worker_queue = json.loads(requests.get(url, auth=(user,password)).text)
    queue_depth = (worker_queue["messages_unacknowledged"])
    return queue_depth

def find_files(directory, extensions):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                yield root, file, file_path

def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    user = os.environ.get('user','celery') 
    password = os.environ.get('password','celery')
    celery_host = os.environ.get('celery_host','192.168.1.110')
    celery_port = os.environ.get('celery_port', '31672')
    celery_vhost = os.environ.get('celery_vhost','celery')
    thing = thing + user + ':' + password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
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

def ffprober(ffprobe_string,file_path):
    subprocess_cmd = ffprobe_string + ' "' + file_path + '"'
    p = subprocess.run(subprocess_cmd, capture_output=True, text=True).stdout
    d = json.loads(p)
    return d

def ffprober2(ffprobe_string,file_path):
    try:
        full_command = f'{ffprobe_string} "{file_path}"'
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Error running ffprobe: {e}"}

