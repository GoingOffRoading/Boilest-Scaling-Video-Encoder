from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

@app.task(queue='worker')
def fencoder(fprober_json):
    # This is the step where we do the actual video encoding
    fencoder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fencoder for ' + fprober_json["file_name"] + ' starting at ' + str(fencoder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    print (json.dumps(fprober_json, indent=3, sort_keys=True))

    # Need to get the ffmpeg settings
    ffmpeg_settings = (fprober_json["ffmpeg_settings"])
    #print ('ffmpeg settings are: ' + ffmpeg_settings)
        
    # Need to get the input filepath
    file_path = (fprober_json["file_path"])
    file_name = (fprober_json["file_name"])
    ffmeg_input_file = os.path.join(file_path,file_name)
    #print ('input file is: ' + ffmeg_input_file)
    
    # Need to get the encoding settings     
    ffmpeg_encoding_settings = (fprober_json["ffmpeg_encoding_string"])
    #print ('encoding settings are: ' + ffmpeg_encoding_settings)
    
    # Need to get the output filepath   
    #file_name = Path(file_name).stem
    #output_extension = (fprober_json["ffmeg_container_extension"])
    
    #print ('filename is currently: ' + file_name)
    
    ffmpeg_output_file = (fprober_json["ffmpeg_output_file"])
    ffmpeg_output_file = '/boil_hold/' + ffmpeg_output_file
    
    # All together now
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + ffmeg_input_file + '"' + ffmpeg_encoding_settings + ' "' + ffmpeg_output_file + '"'
    print ('ffmpeg command:')
    print (ffmpeg_command)    

    # We need to determine if this is a production run and run the function like normal
    if (fprober_json["production_run"]) == 'yes':
        print ('Please hold')
        #os.system(ffmpeg_command)
        process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
        for line in process.stdout:
            print(line)
    elif (fprober_json["production_run"]) == 'no':
        print ('This is a test run, so lets maybe not polute production')
        input_file_stats = float(31.44148)
        output_file_stats = float(34.31477626)
        new_file_size_difference = float(2.873836)
    else:
        print ('Production flag missing from config')
    
    if os.path.exists(ffmeg_input_file and ffmpeg_output_file):
        print (ffmeg_input_file + ' and ' + ffmpeg_output_file + ' Files Exists')
        input_file_stats = os.stat(ffmeg_input_file)
        input_file_stats = round(input_file_stats.st_size / (1024 * 1024))
        print (f'Original file Size in MegaBytes is: ' + str(input_file_stats)) 
        output_file_stats = (os.stat(ffmpeg_output_file))
        output_file_stats = round(output_file_stats.st_size / (1024 * 1024))
        print (f'Encoded file Size in MegaBytes is: ' + str(output_file_stats)) 
        new_file_size_difference = input_file_stats - output_file_stats
        print (f'Total Space savings is:' + str(new_file_size_difference))
        print ('Removing ' + ffmeg_input_file)
        # We're checking for to things:
        # 1) If this is a production run, and we intend to delete source
        # 2) Don't delete sourec if the ffmpeg encode failed

        fencoder_duration = (datetime.now() - fencoder_start_time).total_seconds() / 60.0

        if (fprober_json["production_run"]) == 'yes' and output_file_stats != 0.0:
            os.remove(ffmeg_input_file) 
            ffmpeg_destination = fprober_json["file_path"] + '/' + fprober_json["ffmpeg_output_file"]
            print('Moving ' + ffmpeg_output_file + ' to ' + ffmpeg_destination)
            shutil.move(ffmpeg_output_file, ffmpeg_destination)
            print ('Done')
            fencoder_json = {'old_file_size':input_file_stats, 'new_file_size':output_file_stats, 'new_file_size_difference':new_file_size_difference, 'fencoder_duration':fencoder_duration}
            fencoder_json.update(fprober_json) 
            print(json.dumps(fencoder_json, indent=3, sort_keys=True))
            return fencoder_json
            #fresults.delay(fencoder_json)
        elif output_file_stats == 0.0:
            print ('Something went wrong, and the output file size is 0.0 KB')
            print ('Deleting: ' + ffmpeg_output_file)
            os.remove(ffmpeg_output_file) 
        else:
            print ('Something went wrong, and neither source nor encoded were deleted ')
    else:
        print("Either source or encoding is missing, so exiting")
    
    print ('>>>>>>>>>>>>>>>> fencoder ' + fprober_json["file_name"] + ' complete, executed for ' + str(fencoder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

