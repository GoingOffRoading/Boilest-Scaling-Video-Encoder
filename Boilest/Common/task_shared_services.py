from datetime import datetime
import os, json, requests, shutil, subprocess, logging

def task_start_time(task):
    function_task_start_time = datetime.now()
    logging.debug ('>>>>>>>>>>>>>>>> ' + task + ' starting at ' + str(function_task_start_time) + '<<<<<<<<<<<<<<<<<<<')
    return function_task_start_time

def task_duration_time(task,function_task_start_time):
    function_task_duration_time = (datetime.now() - function_task_start_time).total_seconds() / 60.0
    logging.debug ('>>>>>>>>>>>>>>>> ' + task + ' complete, executed for ' + str(function_task_duration_time) + ' minutes <<<<<<<<<<<<<<<<<<<')


def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    user = os.environ.get('user','celery') 
    password = os.environ.get('password','celery')
    celery_host = os.environ.get('celery_host','192.168.1.110')
    celery_port = os.environ.get('celery_port', '31672')
    celery_vhost = os.environ.get('celery_vhost','celery')
    thing = thing + user + ':' + password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
    logging.debug ('celery_url_path is: ' + thing)
    return thing


def check_queue(queue_name):
    rabbitmq_host = 'http://' + os.environ.get('rabbitmq_host','192.168.1.110')
    rabbitmq_port = os.environ.get('rabbitmq_port','32311')
    user = os.environ.get('user','celery')
    password = os.environ.get('password','celery')
    celery_vhost = os.environ.get('celery_vhost','celery')
    url = rabbitmq_host + ':' + str(rabbitmq_port) + '/api/queues/' + celery_vhost + '/' + queue_name
    logging.debug ('Checking RabbitMQ queue depth for: ' + queue_name)
    worker_queue = json.loads(requests.get(url, auth=(user,password)).text)
    queue_depth = (worker_queue["messages_unacknowledged"])
    logging.debug ('check_queue queue depth is: ' + str(queue_depth))
    return queue_depth

def get_active_tasks(queue_name)-> int:
    from celery import Celery
    try:
        # Create a Celery instance
        app = Celery('get_active_tasks_count', broker = celery_url_path('amqp://'))

        with app.connection() as connection:
            # Create a Celery control object
            celery_control = app.control

            # Inspect active tasks for the specified queue
            active_tasks = celery_control.inspect().active(queue_name)

            if active_tasks is not None and queue_name in active_tasks:
                # Return the count of active tasks in the specified queue 
                logging.debug ('get_active_tasks tasks in-progress for ' + queue_name + ' is: ' + str(len(active_tasks[queue_name])) )
                return len(active_tasks[queue_name])
            else:
                # No active tasks in the specified queue
                logging.debug ('Remaining tasks in progress: 0')
                return 0

    except Exception as e:
        logging.error(f"Error getting active tasks count: {e}")
        return -1 # Return -1 to indicate an error

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

        logging.debug("Contents copied successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def is_directory_empty_recursive(directory_path):
    # Check to see if a directory is empty, return True if Empty
    for root, dirs, files in os.walk(directory_path):
        # If there are any files or subdirectories, the directory is not empty
        if files or dirs:
            return False
    # If the loop completes without returning, the directory and its subdirectories are empty
    return True

def ffprober_function(file_path):
    try:
        ffprobe_string = "ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout -of json"
        file_path = file_path["file_path"]
        full_command = f'{ffprobe_string} "{file_path}"'
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Error running ffprobe: {e}"}

def find_files(directories, extensions):
    for directory in directories:
        logging.info ('Scanning: ' + directory)
        for root, dirs, files in os.walk(directory):
            for file in files:
                for ext in extensions:
                    if file.lower().endswith(ext.lower()):
                        file_path = os.path.join(root, file)
                        result_dict = {
                            'directory': directory,
                            'root': root,
                            'file': file,
                            'file_path': file_path,
                            'extension': ext
                        }
                        yield json.dumps(result_dict)

def ffmpeg_output_file(file_path):
    # Split the file path into the root and extension
    root, extension = os.path.splitext(file_path)    
    # Check if the existing extension is already ".mkv"
    if extension.lower() != '.mkv':
        # Create the new file path with .mkv extension
        new_file_path = root + '.mkv'
    else:
        # If the extension is already ".mkv", return the original file path
        new_file_path = file_path    
    ffmpeg_temp_output = '/boil_hold/' + new_file_path    
    return ffmpeg_temp_output


def validate_video(file_path):
    # This function determines if a video is valid, or if the video contains errors
    # Returns:
    #       Failure if the shell command returns anything; i.e. one of the streams is bad
    #       Success if the shell command doesn't return anything; i.e. the streams are good
    #       Error if the shell command fails; this shouldn't happen
    try:
        command = 'ffmpeg -v error -i "' + file_path + '" -f null -'
        logging.debug (command)
        # Run the shell command and capture both stdout and stderr
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if there is any output (stdout or stderr)
        if result.stdout or result.stderr:
            return "Failure"
        else:
            return "Success"
    except Exception as e:
        return f"Error: {e}"

def run_ffmpeg(ffmpeg_command):
    try:
        process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

        for line in process.stdout:
            logging.debug(line)

        return "Success"
    except Exception as e:
        logging.debug(f"Error: {e}")
        return "Failure"  # Return a non-zero exit code to indicate an error


def get_file_size_bytes(file_path):
    try:
        # Get the size of the file in bytes
        size_bytes = os.path.getsize(file_path)
        return size_bytes
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None