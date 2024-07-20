from celery import Celery
import json, os, logging, subprocess, requests, shutil, mysql.connector
from mysql.connector import Error
from datetime import datetime
import celeryconfig

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
# >>>>>>>>>>>>>>> Celery Configurations >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  


@app.task
def requires_encoding(file_located_data):
    stream_info = ffprobe_function(file_located_data['file_path'])
    encoding_decision = False
    old_file_size = file_size_kb(file_located_data['file_path'])
    processing_priority = get_ffmpeg_processing_priority(old_file_size,stream_info)
    print('processing_priority is: ' + str(processing_priority))
    encoding_decision, ffmepg_output_file_name = check_container_type(stream_info, encoding_decision, file_located_data['file'])
    encoding_decision, ffmpeg_command = check_codecs(stream_info, encoding_decision)
    if encoding_decision == True:
        print ('file needs encoding')
        file_located_data['ffmpeg_command'] = ffmpeg_command
        file_located_data['ffmepg_output_file_name'] = ffmepg_output_file_name
        file_located_data['old_file_size'] = file_size_kb(file_located_data['file_path'])
        print(json.dumps(file_located_data, indent=4))
        process_ffmpeg.apply_async(kwargs={'file_located_data': file_located_data}, priority=6)
    else:
        print ('file does not need encoding')
    print (encoding_decision)
    print (ffmpeg_command)


def get_ffmpeg_processing_priority(old_file_size,stream_info):
    priority = 6
    print('Starting with priority: ' + str(priority))
    if old_file_size > 1000000:
        priority = priority -1
        print('File is large, priority is now: ' + str(priority))
    if stream_info["streams"][0]["codec_name"] != "av1":
        priority = priority -1
        print('Video is not AV1, priority is now: ' + str(priority))
    if stream_info['format'].get('format_name') != "matroska,webm":
        priority = priority -1
        print('Format is not MKV, priority is now: ' + str(priority))
    return priority


def file_size_kb(file_path):
    # Returns the file size of the file_path on disk
    if os.path.isfile(file_path):
        file_size_bytes = os.path.getsize(file_path)
        file_size_kb = file_size_bytes / 1024
        return round(file_size_kb)
    else:
        return 0.0


def ffprobe_function(file_path):
    # Subprocess call to ffprobe to retrieve video info in JSON format
    ffprobe_command = f'ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout,format=nb_streams -of json "{file_path}"'
    result = subprocess.run(ffprobe_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stream_info = json.loads(result.stdout)
    return stream_info


def check_container_type(stream_info, encoding_decision, file):
    # Desired container is MKV so we check for that, and pass True for all other container types
    format_name = stream_info['format'].get('format_name')
    print ('format is: ' + format_name)
    if format_name != 'matroska,webm':
        encoding_decision = True
    encoding_decision, ffmepg_output_file = check_container_extension(file, encoding_decision)
    print ('>>>check_container_type<<<  Container is: ' + format_name + ' so, encoding_decision is: ' + str(encoding_decision))
    return encoding_decision, ffmepg_output_file
    

def check_container_extension(file, encoding_decision):
    base, ext = os.path.splitext(file)
    if ext.lower() != '.mkv':
        # Change the extension to .mkv
        file = base + '.mkv'
        encoding_decision = True
    ffmepg_output_file = '/boil_hold/' + file
    return encoding_decision, ffmepg_output_file


def check_codecs(stream_info, encoding_decision):
    # Loops through the streams in stream_info from requires_encoding, then
    # calls functions to determine if the steam needs encoding based on stream type conditions 
    streams_count = stream_info['format']['nb_streams']
    ffmpeg_command = str()
    print ('There are : ' + str(streams_count) + ' streams')
    for i in range (0,streams_count):
        codec_type = stream_info['streams'][i]['codec_type'] 
        if codec_type == 'video':
            encoding_decision, ffmpeg_command = check_video_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'audio':
            encoding_decision, ffmpeg_command = check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'subtitle':
            encoding_decision, ffmpeg_command = check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'attachment':
            encoding_decision, ffmpeg_command = check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command)        
    return encoding_decision, ffmpeg_command


def check_video_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the video stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    desired_video_codec = 'av1'
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    if codec_name == desired_video_codec:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name == 'mjpeg':
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name != desired_video_codec: 
        encoding_decision = True
        svt_av1_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + svt_av1_string
    else:
        print ('ignoring for now')
    return encoding_decision, ffmpeg_command


def check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the audio stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_audio_codec = 'aac'
    #if codec_name != desired_video_codec:
    #    encoding_decision = True
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
    return encoding_decision, ffmpeg_command
    

def check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the subtitle stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_subtitle_codec = 'srt'
    #if codec_name != desired_subtitle_codec:
    #    encoding_decision = True
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
    return encoding_decision, ffmpeg_command


def check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the attachment stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_attachment_codec = '???'
    #if codec_name != desired_attachment_codec:
    #    encoding_decision = True
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
    return encoding_decision, ffmpeg_command
