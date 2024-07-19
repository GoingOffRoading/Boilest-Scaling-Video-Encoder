from celery import Celery
import json, os, logging, subprocess, requests, shutil, mysql.connector
from mysql.connector import Error
from datetime import datetime
import celeryconfig

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
# >>>>>>>>>>>>>>> Celery Configurations >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  


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

app = Celery('worker', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)


# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the actual processing of media fules
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<
 

@app.task()
def process_ffmpeg(file_located_data):
    file = file_located_data['file']
    if ffmpeg_prelaunch_checks(file_located_data) == True:
        print(file + ' has passed ffmpeg_prelaunch_checks')
        if run_ffmpeg(file_located_data) == True:
            print(file + ' has passed run_ffmpeg')
            if ffmpeg_postlaunch_checks(file_located_data) == True:
                print(file + ' has passed ffmpeg_postlaunch_checks')
                if move_media(file_located_data) == True:
                    print(file + ' has passed move_media')
                    file_path = file_located_data['file_path']
                    ffmepg_output_file_name = file_located_data['ffmepg_output_file_name'] 
                    file_located_data['new_file_size'] = get_file_size_kb(destination_file_name_function(file_path, ffmepg_output_file_name))
                    write_results.apply_async(kwargs={'file_located_data': file_located_data}, priority=3)
                    print(json.dumps(file_located_data, indent=4))


################# Pre Launch Checks #################

def ffmpeg_prelaunch_checks(file_located_data):
    pre_launch_file_path = file_located_data['file_path']
    pre_launch_old_file_size = file_located_data['old_file_size']
    if prelaunch_file_exists(pre_launch_file_path):
        if prelaunch_hash_match(pre_launch_file_path, pre_launch_old_file_size):
            if prelaunch_file_validation(pre_launch_file_path):
                return True
    else:
        return False


def prelaunch_file_exists(file_path):
    #  Checks to see if the input file still exists, returns True on existance
    if file_exists(file_path):
        print(str(file_path) + ' Exists')
        return True
    else:
        print(str(file_path) + ' Does Not Exists')
        return False


def prelaunch_hash_match(file_path, pre_launch_old_file_size):
    current_file_hash = get_file_size_kb(file_path)
    if pre_launch_old_file_size == current_file_hash:
        print(str(file_path) + ' matches its hash')
        return True
    else:
        print (str(file_path) + ' does not match its hash')
        return False


def prelaunch_file_validation(file_path):
    if validate_video(file_path):
        print(str(file_path) + ' passed validation')
        return True
    else:
        print(str(file_path) + ' failed validation')
        return False    


################# Run FFMPEG  #################

def run_ffmpeg(file_located_data):
    # Command to run ffmpeg in subprocess
    ffmpeg_string_settings = 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i'
    ffmpeg_stringfile_path = file_located_data['file_path']
    ffmpeg_stringffmpeg_command = file_located_data['ffmpeg_command']
    ffmpeg_stringffmepg_output_file_name = file_located_data['ffmepg_output_file_name']
    output_ffmpeg_command = f"{ffmpeg_string_settings} \"{ffmpeg_stringfile_path}\" {ffmpeg_stringffmpeg_command} \"{ffmpeg_stringffmepg_output_file_name}\""
    print ('ffmpeg_command is: ' + output_ffmpeg_command)
    print ('running ffmpeg now')
    try:
        process = subprocess.Popen(output_ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
        for line in process.stdout:
            print(line)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False  # Return a non-zero exit code to indicate an error


################# Post Launch Checks #################


def ffmpeg_postlaunch_checks(file_located_data):  
    post_launch_original_file = file_located_data['file_path']
    post_launch_encoded_file = file_located_data['ffmepg_output_file_name']
    if post_launch_file_check(post_launch_original_file, post_launch_encoded_file):
        if post_launch_file_validation(post_launch_encoded_file):
            return True
    else:
        print('ffmpeg_postlaunch_checks failed')
        return False


def post_launch_file_check(post_launch_original_file, post_launch_encoded_file):
    # Check to see if the original file, and the encoded file are there
    if file_exists(post_launch_original_file) and file_exists(post_launch_encoded_file):
        print(str(post_launch_encoded_file) + ' passed post_launch_file_check')
        return True
    else:
        print(str(post_launch_encoded_file) + ' failed post_launch_file_check')
        return False
    

def post_launch_file_validation(post_launch_encoded_file):
    print('Starting post_launch_file_validation')
    if validate_video(post_launch_encoded_file) == True:
        print(str(post_launch_encoded_file) + ' passed post_launch_file_validation')
        return True
    else:
        print(str(post_launch_encoded_file) + ' failed post_launch_file_validation')
        return False


################# move_media #################


def move_media(file_located_data):
    file_path = file_located_data['file_path']
    renamed_file = renamed_file_function(file_path)
    ffmepg_output_file_name = file_located_data['ffmepg_output_file_name']
    destination_file_name = destination_file_name_function(file_path, ffmepg_output_file_name)
    if rename_original_file_function(file_path, renamed_file):
        if move_encoded_file_function(ffmepg_output_file_name, destination_file_name):
            if delete_renamed_original_file_function(renamed_file):
                return True
    else:
        return False


def renamed_file_function(file_to_be_renamed):
    renamed_directory, renamed_filename = os.path.split(file_to_be_renamed)
    rename, reext = os.path.splitext(renamed_filename)
    new_filename = f"{rename}-copy{reext}"
    new_file_path = os.path.join(renamed_directory, new_filename)
    return new_file_path


def destination_file_name_function(file_path, ffmepg_output_file_name):
    # Quick and silly function for creating the correct filepath to move the encoded file to
    destination_file_name = os.path.join(os.path.dirname(file_path), os.path.basename(ffmepg_output_file_name))
    return destination_file_name


def rename_original_file_function(file_path, renamed_file):
    # This is here incase any of the move opperations mess up
    try:
        os.rename(file_path, renamed_file)
    except Exception as e:
        print(f"An error occurred: {e}")
    if file_exists(renamed_file) == True:
        print(file_path + ' passed rename_original_file')
        return True
    else:
        print(file_path + ' filed rename_original_file')
        return False


def move_encoded_file_function(ffmepg_output_file_name, destination_file_name):
    # Function to move the encoded file to the original file's directory
    try:
        shutil.move(ffmepg_output_file_name, destination_file_name) 
    except Exception as e:
        print(f"An error occurred: {e}")
    if file_exists(destination_file_name) == True:
        print(destination_file_name + ' has passed move_encoded_file')
        return True
    else:
        print(destination_file_name + ' has failed move_encoded_file')
        return False     
        

def delete_renamed_original_file_function(renamed_file):
    # Function to delete the renamed original file
    try:
        os.remove(renamed_file)
    except Exception as e:
        print(f"An error occurred: {e}")
    if file_exists(renamed_file) == True:
        print(renamed_file + ' has failed delete_renamed_original_file_function')
        return False
    else:
        print(renamed_file + ' has passed delete_renamed_original_file_function')
        return True        

########################## Common Functions ##########################

def file_exists(filepath):
    file_existance = os.path.isfile(filepath)
    # Returns true if the file that is about to be touched is in the expected location
    print (filepath + ' : ' + str(file_existance))
    return file_existance

def get_file_size_kb(filepath_for_size_kb):
    print('filepath is: ' + str(filepath_for_size_kb))
    file_size_bytes = os.path.getsize(filepath_for_size_kb)
    file_size_kb = round(file_size_bytes / 1024)
    return file_size_kb

def validate_video(filepath):
    # This function determines if a video is valid, or if the video contains errors
    # Returns:
    #       Failure if the shell command returns anything; i.e. one of the streams is bad
    #       Success if the shell command doesn't return anything; i.e. the streams are good
    #       Error if the shell command fails; this shouldn't happen
    try:
        command = 'ffmpeg -v error -i "' + filepath + '" -f null -'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout or result.stderr:
            print ('File failed validation')
            return False
        else:
            print ('File passed validation')
            return True
    except Exception as e:
        return f"Error: {e}"
    

# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the files by searching directories
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

@app.task
def write_results(file_located_data):
    unique_identifier = file_located_data['file'] + str(datetime.now().microsecond)
    file_name = file_located_data['file']
    file_path = file_located_data['file_path']
    config_name = 'placeholder'
    new_file_size = file_located_data['new_file_size']
    old_file_size = file_located_data['old_file_size']
    new_file_size_difference = old_file_size - new_file_size
    watch_folder = file_located_data['directory']
    ffmpeg_encoding_string = file_located_data['ffmpeg_command']

    print('Writing results')
    insert_record(unique_identifier, file_name, file_path, config_name, new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string)
    print('Writing results complete')


def insert_record(unique_identifier, file_name, file_path, config_name, new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string):
    try:
        # Connection details
        connection = mysql.connector.connect(
            host='192.168.1.110',
            port=32053,  # replace with your non-default port
            database='boilest',
            user='boilest',
            password='boilest'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            recorded_date = datetime.now()  # Current date and time
            
            insert_query = """
                INSERT INTO ffmpeghistory (
                    unique_identifier, recorded_date, file_name, file_path, config_name,
                    new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            record = (
                unique_identifier, recorded_date, file_name, file_path, config_name,
                new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string
            )
            
            cursor.execute(insert_query, record)
            connection.commit()
            print("Record inserted successfully")
            
    except Error as e:
        print(f"Error while connecting to MariaDB: {e}")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MariaDB connection is closed")

