from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib
from task_shared_services import celery_url_path, file_size_mb

backend_path = celery_url_path('rpc://') 
broker_path = celery_url_path('amqp://') 
app = Celery('tasks', backend = backend_path, broker = broker_path)

@app.task(queue='worker')
def fencoder(json_configuration):

    ffmpeg_settings = os.environ.get('ffmpeg_settings','-hide_banner -loglevel 16 -stats -stats_period 10')

    file_path = json_configuration["file_path"]
    output_file = json_configuration["output_filename"]
    root = json_configuration["root"]
    temp_filepath = '/boil_hold/' +  output_file
    ffmpeg_command = json_configuration["ffmpeg_command"]
    file = json_configuration["file"]

    
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + file_path + '" ' + ffmpeg_command + ' "' + temp_filepath + '"'
    print (ffmpeg_command)

    print ('Please hold')
    
    process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    for line in process.stdout:
        print(line)

    if os.path.exists(file_path and temp_filepath):
        file_path_stats = file_size_mb(file_path)
        print ('old ' + file + ' was: '+ str(file_path_stats))
        temp_filepath_stats = file_size_mb(file_path)
        print ('new ' + output_file + ' is: '+ str(temp_filepath_stats))
        encoded_stats_difference = file_path_stats - temp_filepath_stats
        print ('Spave saved was: '+ str(encoded_stats_difference))

        if temp_filepath_stats != 0.0:
            destination_filepath = root + '/' + output_file
            print('Moving ' + temp_filepath + ' to ' + destination_filepath)
            os.remove(file_path)
            shutil.move(temp_filepath, destination_filepath) 
        elif temp_filepath_stats == 0.0:
            print('Problem with the output')
            os.remove(temp_filepath_stats)

    else:
        print('Something went wrong, a file is missing')
    