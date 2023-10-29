from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, pathlib

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

@app.task(queue='worker')
def fencoder(ffinder_json):
    
    fencoder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fprober for ' + ffinder_json["file_name"] + ' starting at ' + str(fencoder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # Using subprocess to call FFprobe, get JSON back on the video's container, and streams, then display the outputs  
    file_path = (ffinder_json["file_path"])
    file_name = (ffinder_json["file_name"])
    file_full_path = os.path.join(file_path,file_name)    
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout', '-of', 'json', file_full_path]
    print ("ffprobe's command on " + file_name + ":")
    print (cmnd)
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)
    print ("ffprobe's results on " + file_name + ":")
    print(json.dumps(d, indent=3, sort_keys=True))

    # Setting starter variables.  These are revisited throughout the loop.
    encode_string = str()
    encode_decision = 'no'
    
    # Determine if the container needs to be changed
    original_container = (d['format']['format_name'])
    print ('Original Video container is: ' + original_container)
    if original_container != 'matroska,webm' or pathlib.Path(ffinder_json["file_name"]).suffix != '.mkv':
        file_name = (ffinder_json["file_name"])
        file_name = Path(file_name).stem 
        ffmpeg_output_file = file_name + '.mkv'
        encode_decision = 'yes'
        print ('Container is not MKV, converting container')
    else:
        ffmpeg_output_file = file_name
        print (file_name + ' is already .mkv, no need to change container')
    
    # Stream Loop: We need to loop through each of the streams, and make decisions based on the codec in the stream
    streams_count = d['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    for i in range (0,streams_count):
        if d['streams'][i]['codec_type'] == 'video':
            codec_name = d['streams'][i]['codec_name'] 
            if codec_name == 'av1':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != 'av1':
                encode_decision = 'yes'
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_video_string"])
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the video codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        elif d['streams'][i]['codec_type'] == 'audio':
            codec_name = d['streams'][i]['codec_name'] 
            if codec_name == 'opus':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:a copy'
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
                # No need to change encode_decision as the audio codec is in the desired format
            elif codec_name != 'opus' and d['streams'][i]['channel_layout'] == '5.1(side)':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus -af aformat=channel_layouts="7.1|5.1|stereo"'
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ' and, using ' + d['streams'][i]['channel_layout'] +', filtering, then encoding stream')
                # encode_decision = yes as the audio codec is not in the desired format... libopus has problems with 5.1(side) channel layout in ffmpeg so we catch it here.  Unclear if we can combine this step with the next one
            elif codec_name != 'opus':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus' 
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the audio codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        elif d['streams'][i]['codec_type'] == 'subtitle':
            codec_name = d['streams'][i]['codec_name'] 
            if codec_name == 'subrip':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy'
                # No need to change encode_decision as the subtitles are in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
            elif codec_name != 'subrip' and d['streams'][i]['codec_name'] == 'hdmv_pgs_subtitle':
                # These are image based subtitles, and can't be converted to text type
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy' 
                # No need to change encode_decision as we can't change picture subtitles into text subtitles
                print ('Stream ' + str(i) + ' is ' + codec_name + ': a pain in the dick, and nothing we can do but copy the stream')
            elif codec_name != 'subrip':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -scodec subrip' 
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
            else:
                print ('Something is broken with stream ' + str(i))

        # No idea if attachments provide any value.  Sr far: no
        elif d['streams'][i]['codec_type'] == 'attachment':
            print ('Stream is attachment, ignore')
            # Progably not a great idea to ditch these, but whatever.  So far in discovery, the attachments have been font files.         
        else:
            print ('fuck')

    # Need to get the ffmpeg settings
    ffmpeg_settings = (ffinder_json["ffmpeg_settings"])
    #print ('ffmpeg settings are: ' + ffmpeg_settings)
    # Need to get the input filepath
    file_full_path = os.path.join(file_path,file_name)
    #print ('input file is: ' + ffmeg_input_file)
    ffmpeg_output_file_path = '/boil_hold/' + ffmpeg_output_file    

    if encode_decision == 'yes':
        # All together now
        ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + file_full_path + '"' + encode_string + ' "' + ffmpeg_output_file_path + '"'
        print ('ffmpeg command:')
        print (ffmpeg_command)    


        process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
        for line in process.stdout:
            print(line)
    elif encode_decision == 'no':
        print ('Encode Decision was no')
    else:
        print ('Something went wrong')
        
    if os.path.exists(file_full_path and ffmpeg_output_file_path):
        print (file_full_path + ' and ' + ffmpeg_output_file_path + ' Files Exists')
        input_file_stats = os.stat(file_full_path)
        input_file_stats = round(input_file_stats.st_size / (1024 * 1024))
        print (f'Original file Size in MegaBytes is: ' + str(input_file_stats)) 
        output_file_stats = (os.stat(ffmpeg_output_file_path))
        output_file_stats = round(output_file_stats.st_size / (1024 * 1024))
        print (f'Encoded file Size in MegaBytes is: ' + str(output_file_stats)) 
        new_file_size_difference = input_file_stats - output_file_stats
        print (f'Total Space savings is:' + str(new_file_size_difference))
        print ('Removing ' + file_full_path)
        if output_file_stats != 0.0:
            os.remove(file_full_path) 
            ffmpeg_destination = file_path + '/' + ffmpeg_output_file
            print('Moving ' + ffmpeg_output_file_path + ' to ' + ffmpeg_destination)
            shutil.move(ffmpeg_output_file_path, ffmpeg_destination)
            print ('Done')
            fencoder_json = {'old_file_size':input_file_stats, 'new_file_size':output_file_stats, 'new_file_size_difference':new_file_size_difference}
            #, 'fencoder_duration':fencoder_duration}
            fencoder_json.update(ffinder_json) 
            print(json.dumps(fencoder_json, indent=3, sort_keys=True))
            return fencoder_json
        elif output_file_stats == 0.0:
            print ('Something went wrong, and the output file size is 0.0 KB')
            print ('Deleting: ' + ffmpeg_output_file)
            os.remove(ffmpeg_output_file) 
        else:
            print ('Something went wrong, and neither source nor encoded were deleted ')
    else:
        print("Either source or encoding is missing, so exiting")

    fencoder_duration = (datetime.now() - fencoder_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> fencoder ' + ffinder_json["file_name"] + ' complete, executed for ' + str(fencoder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

